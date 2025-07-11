import streamlit as st
import base64
import os

st.set_page_config(layout="wide")
st.title("PDF Viewer")

# st.write(st.session_state)
pdf_file = st.session_state.get("selected_file")

if pdf_file and os.path.exists(pdf_file):
    print("WORKING")
    with open(pdf_file, "rb") as f:
        pdf_bytes = f.read()
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="900px" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
else:
    st.error("No PDF file selected or file does not exist. Please select a valid PDF file from the previous page.")
    st.write(st.session_state)
