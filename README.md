LINK TO DASHBOARD (Please allow some time for loading): https://ameya-t-teikotechnical-ameyat-main-ki65od.streamlit.app/


INSTRUCTIONS FOR RUNNING IN GITHUB CODESPACES:

pip install -r requirements.txt

then in terminal, streamlit run main.py will generate the dashboard with all the relevant tables and data locally. 

If individual functions need to be run separately, please add the below to queries.py:

create_db()
load_data()

create_freq_summary()
print(display_freq_summary())

print(treatment_response())
box = treatment_box_plot()
plt.show(box)
print(treatment_report())

full_subset, samples_per_proj, responder_cnt, subject_gender = subset_analytics()
print(full_subset)
print(samples_per_proj)
print(responder_cnt)
print(subject_gender)

print(assessment_question()) #this is for the question in the google form

Then, Python queries.py in the terminal. 

However, all the data above will be present in the dashboard. 


RELATIONAL DATABASE SCHEMA RATIONALE:

I split the initial data into 3 separate tables, cell_subjects, cell_samples, and cell_counts. 
Cell_subjects houses the metadata for the patients themselves, and don't need to be repeated per sample.
Cell_samples houses the info for all the samples, and links to subjects via subject_id, since there is a one-to-many relationship between subjects and samples.
Similarly, there is a one-to-many relationship between samples and their cell counts, so the counts are housed separately.
Furthermore, in cell_counts, rather than having one column per different cell type (which would be hard to scale if more types were added) I added a cell_type column to be associated with a count.
While this does increase the number of rows in the table, it allows us to potentially add more cell types without altering the schema. 
This design will be able to handle more projects and samples without disrupting query times. 


CODE STRUCTUTE EXPLANATION:

To structure the code, I followed the general outline of each analysis that was needed. I created several functions that generated specific tables that pertain to specific analytics. 
First, I have the create and load functions, which create and populate the tables with the data from the csv. Next, separate functions house queries that relate to frequency summaries, 
Miraclib response analytics, and subset analytics for the specifications. The functions mostly return dataframes (and one boxplot figure) so that it is easy to implement them in the 
Streamlit dashboard, and additionally easy to print to console if needed. To fill the dashboard, I simple needed to import the functions and call them as needed. I added docstrings
to each function for commenting purposes. 





