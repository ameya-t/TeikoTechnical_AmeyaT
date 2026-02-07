import sqlite3

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import shapiro, mannwhitneyu

DB_NAME = 'cell_data.db'
CELL_DATA_FILE = 'cell-count.csv'

def create_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS cell_subjects(
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project TEXT,
            subject TEXT UNIQUE,
            condition TEXT,
            age INTEGER,
            sex TEXT,
            treatment TEXT,
            response TEXT
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS cell_samples(
            sample TEXT PRIMARY KEY,
            subject_id INTEGER,
            sample_type TEXT,
            time_from_treatment_start INTEGER,
            FOREIGN KEY(subject_id) REFERENCES cell_subjects(subject_id) 
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS cell_counts(
            count_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample TEXT,
            cell_type TEXT,
            count INTEGER,
            FOREIGN KEY(sample) REFERENCES cell_samples(sample) 
        );
    """)

    conn.commit()
    conn.close()

def load_data():

    data = pd.read_csv(CELL_DATA_FILE)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    for index, row in data.iterrows():
        c.execute('''
            INSERT OR IGNORE INTO cell_subjects (project, subject, condition, age, sex, treatment, response) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['project'],
            row['subject'],
            row['condition'],
            row['age'],
            row['sex'],
            row['treatment'],
            row['response']
        ))

    conn.commit()

    for index, row in data.iterrows():
        c.execute('SELECT subject_id FROM cell_subjects WHERE subject = ?', (row['subject'],))
        subject_id = c.fetchone()[0]

        c.execute('''
            INSERT OR IGNORE INTO cell_samples (sample, subject_id, sample_type, time_from_treatment_start) VALUES (?, ?, ?, ?)
        ''', (
            row['sample'],
            subject_id,
            row['sample_type'],
            row['time_from_treatment_start']
        ))

    conn.commit()

    split_data = data.melt(id_vars=['sample'], value_vars=['b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte'],
                           var_name='cell_type', value_name='count').dropna()

    for index, row in split_data.iterrows():
        c.execute('''
            INSERT OR IGNORE INTO cell_counts (sample, cell_type, count) VALUES (?, ?, ?)
        ''', (
            row['sample'],
            row['cell_type'],
            row['count']
        ))

    conn.commit()
    conn.close()

    print('Database created and data loaded!')

def clear_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS cell_counts;")
    c.execute("DROP TABLE IF EXISTS cell_samples;")
    c.execute("DROP TABLE IF EXISTS cell_subjects;")
    c.execute("DROP TABLE IF EXISTS frequency_summary;")


    conn.commit()
    conn.close()


def create_freq_summary():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS frequency_summary AS 
            WITH total_cell_counts AS (
                SELECT sample, SUM(count) as total_count FROM cell_counts GROUP BY sample
            ) SELECT c.sample, t.total_count, c.cell_type AS population, c.count, ROUND(c.count * 1.0 / t.total_count * 100, 2) as percentage
            FROM cell_counts c JOIN total_cell_counts t ON c.sample = t.sample ORDER BY c.sample;
    ''')

    conn.commit()
    conn.close()

def display_freq_summary():
    conn = sqlite3.connect(DB_NAME)

    summary = '''SELECT * FROM frequency_summary;'''

    res = pd.read_sql_query(summary, conn)

    conn.close()

    return res

def treatment_response():
    conn = sqlite3.connect(DB_NAME)

    compare = '''
        SELECT f.population, sub.response, ROUND(AVG(f.percentage),2) as avg_percentage
        FROM frequency_summary f JOIN cell_samples sam ON f.sample = sam.sample
        JOIN cell_subjects sub ON sam.subject_id = sub.subject_id
        WHERE sub.condition = 'melanoma' and sub.treatment = 'miraclib' and sam.sample_type = 'PBMC'
        GROUP BY f.population, sub.response ORDER BY f.population, sub.response;
    '''

    res = pd.read_sql_query(compare, conn)

    conn.close()

    return res

def treatment_box_plot():
    conn = sqlite3.connect(DB_NAME)

    compare = '''
            SELECT f.sample, f.population, sub.response, f.percentage
            FROM frequency_summary f JOIN cell_samples sam ON f.sample = sam.sample
            JOIN cell_subjects sub ON sam.subject_id = sub.subject_id
            WHERE sub.condition = 'melanoma' and sub.treatment = 'miraclib' and sam.sample_type = 'PBMC';
        '''

    res = pd.read_sql_query(compare, conn)

    fig, axs = plt.subplots(figsize=(10, 5.15))
    sns.boxplot(x='response', y='percentage', hue='population', data=res, gap=0.2)
    axs.set_title('Immune Cell Population Frequency by Response')
    axs.set_ylabel('Relative Frequency (%)')
    axs.set_xlabel('Response')

    conn.close()

    return fig

def treatment_report():
    conn = sqlite3.connect(DB_NAME)

    compare = '''
                SELECT f.sample, f.population, sub.response, f.percentage
                FROM frequency_summary f JOIN cell_samples sam ON f.sample = sam.sample
                JOIN cell_subjects sub ON sam.subject_id = sub.subject_id
                WHERE sub.condition = 'melanoma' and sub.treatment = 'miraclib' and sam.sample_type = 'PBMC';
            '''

    res = pd.read_sql_query(compare, conn)

    mw_test = []
    mw_test_df = pd.DataFrame()

    for c_type in res['population'].unique():
        yes_response = res[(res['population'] == c_type) & (res['response'] == 'yes')]['percentage']
        no_response = res[(res['population'] == c_type) & (res['response'] == 'no')]['percentage']

        #y_stat, y_p = shapiro(yes_response)
        #n_stat, n_p = shapiro(no_response)

        stat, p = mannwhitneyu(yes_response, no_response)

        mw_test.append({'population': c_type, 'median_yes_response': yes_response.median(), 'median_no_response': no_response.median(), 'p_value': p})

        mw_test_df = pd.DataFrame(mw_test)

        mw_test_df['adjusted_p'] = mw_test_df['p_value'] * len(mw_test_df)
        mw_test_df['Signifcant? (adj_p < 0.05)'] = np.where(mw_test_df['adjusted_p'] < 0.05, 'Yes', 'No')


    conn.close()

    return mw_test_df

def subset_analytics():
    conn = sqlite3.connect(DB_NAME)

    subset = '''WITH subset AS (
            SELECT sub.project, sub.subject_id, sub.response, sub.sex, sam.sample
            FROM cell_subjects sub JOIN cell_samples sam ON sub.subject_id = sam.subject_id
            WHERE sub.condition = 'melanoma' AND sub.treatment = 'miraclib' AND sam.sample_type = 'PBMC'
            AND sam.time_from_treatment_start = 0) '''

    full_subset = pd.read_sql_query(subset + "SELECT * FROM subset;", conn)
    samples_per_proj = pd.read_sql_query(subset + "SELECT project, COUNT(sample) as sample_count FROM subset GROUP BY project;", conn)
    responder_cnt = pd.read_sql_query(subset + "SELECT response, COUNT(DISTINCT subject_id) AS subject_count FROM subset GROUP BY response;", conn)
    subject_gender = pd.read_sql_query(subset + "SELECT sex, COUNT(DISTINCT subject_id) AS subject_count FROM subset GROUP BY sex;", conn)

    conn.close()

    return full_subset, samples_per_proj, responder_cnt, subject_gender



















