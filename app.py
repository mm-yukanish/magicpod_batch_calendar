import streamlit as st
import subprocess

# Modern stylish CSS
st.markdown(
    """
    <style>
    body {
        background: #eaf6fb !important;
        font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif !important;
    }
    .main {
        background: transparent !important;
    }
    .stApp {
        background: linear-gradient(120deg, #19f0e8 0%, #1cb5fc 100%) !important;
        min-height: 100vh;
        padding: 0;
    }
    .stButton > button {
        background: #2d3e50;
        color: #fff;
        border-radius: 12px;
        font-size: 1.2em;
        font-weight: 600;
        padding: 0.7em 2.2em;
        border: none;
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
        margin-top: 1.5em;
        margin-bottom: 1.5em;
        cursor: pointer;
        transition: background 0.2s;
    }
    .stButton > button:hover {
        background: #1cb5fc;
        color: #2d3e50;
    }
    .calendar-link-btn {
        display: inline-block;
        background: #1cb5fc;
        color: #fff !important;
        border-radius: 10px;
        font-size: 1.1em;
        font-weight: 600;
        padding: 0.6em 2em;
        text-decoration: none;
        margin-top: 1em;
        margin-bottom: 1em;
        box-shadow: 0 2px 8px rgba(0,0,0,0.10);
        transition: background 0.2s;
    }
    .calendar-link-btn:hover {
        background: #2d3e50;
        color: #fff !important;
    }
    .stAlert, .stSuccess, .stInfo, .stError {
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        font-size: 1.1em;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #2d3e50;
        font-weight: 800;
        letter-spacing: 1px;
    }
    .stMarkdown h1 {
        font-size: 2.6em;
        margin-bottom: 0.2em;
    }
    .stMarkdown h2 {
        font-size: 2em;
        margin-bottom: 0.5em;
    }
    .stMarkdown h3 {
        font-size: 1.5em;
        margin-bottom: 0.5em;
    }
    .stContainer {
        background: #fff;
        border-radius: 18px;
        box-shadow: 0 2px 16px rgba(0,0,0,0.10);
        padding: 2.5em 2em 2em 2em;
        margin: 2em auto 2em auto;
        max-width: 600px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("MagicPod Batch Calendar Generator")

if st.button("Generate a calendar"):
    result = subprocess.run(["python3", "mp_batch.py"], capture_output=True, text=True)
    if result.returncode == 0:
        st.success("Calendar generated!")
        st.markdown("""
            <a href='https://macromill.atlassian.net/wiki/spaces/~71202097f8400394ea4802b63a42e2933709eb/pages/1041858569/MagicPod+Batch+Schedule#MagicPod-Batch-Schedule' target='_blank' class='calendar-link-btn'>Open Calendar</a>
        """, unsafe_allow_html=True)
    else:
        st.error("Error generating calendar:")
        st.text(result.stderr)
else:
    st.info("Click the button to generate the batch schedule calendar.")

st.markdown('</div>', unsafe_allow_html=True) 