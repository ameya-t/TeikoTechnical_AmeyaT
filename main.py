import queries as qr
import streamlit as st

def create_dashboard():
    """
        create_dashboard() creates the interactive dashboard to display all data
        Args: None
        Returns: Nothing
    """


    st.set_page_config(layout="wide")
    st.title("Loblaw Bio: Immune Cell Clinical Trial")

    def create_spacing(n):
        """
            create_spacing(n) creates vertical spacing of n
            Args: n, the number of new lines needed
            Returns: Nothing
        """
        for _ in range(n):
            st.write('')

    #Create and Load Tables
    qr.create_db()
    qr.load_data()

    #Display Frequency Summary
    create_spacing(2)
    st.header('Frequency Summary')
    create_spacing(1)
    st.subheader('Relative Cell Population Frequency Per Sample')
    qr.create_freq_summary()
    st.dataframe(qr.display_freq_summary(), use_container_width=True)
    st.divider()

    #Display Miraclib Treatment Response Summary
    st.header('Miraclib Treatment Response Summary')
    create_spacing(1)
    col1, col2 = st.columns([2, 2])
    with col1:
        st.subheader('Average Cell Population Frequency Per Response')
        st.dataframe(qr.treatment_response(), use_container_width=True)
        st.subheader('Cell Population Frequency Difference Significance (Mann-Whitney U-test)')
        st.dataframe(qr.treatment_report(), use_container_width=True)

    with col2:
        st.subheader('Immune Cell Population Frequency By Response Box Plot')
        st.pyplot(qr.treatment_box_plot())

    create_spacing(1)
    st.subheader('Conclusion')
    create_spacing(1)
    conclusion = '''
        Since the cell population frequency data was of non-normal distribution comparing two groups (responders vs. non-responders) for each population, Mann-Whitney U-tests were run in order to determine the significance in the difference of the 
        frequencies between the two groups. To control the false positive error rate, the p-values were adjusted via Bonferroni
        correction. As seen in the Cell Population Frequency Difference Significance table, none of the differences were 
        statistically significant.
    '''
    st.markdown(f"<div style='font-size:20px; line-height:1.5;'>{conclusion}</div>", unsafe_allow_html=True)

    st.divider()

    #Display Subset Analysis
    full_subset, samples_per_proj, responder_cnt, subject_gender = qr.subset_analytics()

    st.header('Subset Analysis')
    create_spacing(1)
    st.subheader('Miraclib Treated PBMC Melanoma Baseline Samples')
    st.dataframe(full_subset, use_container_width=True)
    create_spacing(1)

    col3, col4, col5 = st.columns(3)
    with col3:
        st.subheader('Baseline Samples Per Project')
        st.dataframe(samples_per_proj, use_container_width=True)
    with col4:
        st.subheader('Baseline Subject Responder Count')
        st.dataframe(responder_cnt, use_container_width=True)
    with col5:
        st.subheader('Subject Gender Count')
        st.dataframe(subject_gender, use_container_width=True)

    st.divider()

if __name__ == "__main__":
    create_dashboard()