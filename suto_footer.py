import streamlit as st


def show_suto_footer():

    st.divider()

    st.markdown(
        """
        <div style="
            text-align:center;
            color:#666666;
            font-size:12px;
            padding:10px;
        ">
        SUTO iTEC Indonesia<br>
        Industrial Reporting & Analytics Engine<br>
        Version 1.0<br> 
        Created by Cahyadi Wisnu Wardana. MM
        </div>
        """,
        unsafe_allow_html=True
    )
