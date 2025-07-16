import streamlit as st
import base64
import os
from pdf_to_knowledge_final import convert_pdf_to_json, extract_text_from_json, load_azure_credentials
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from dotenv import load_dotenv
import requests
import time
import io
import json
import fitz  # PyMuPDF
import pathlib

st.set_page_config(layout="wide")

st.write(st.session_state)

# Set up default state
if "active_view" not in st.session_state:
    st.session_state.active_view = "pdf"  # default to PDF Viewer

# ------------------------------
# Navigation Bar
# ------------------------------
with st.container():
    st.markdown("""
        <style>
        .uniform-button button {
            width: 100% !important;
        }
        .stTitle {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([3, 1, 1, 1])

    with nav_col1:
        st.title("PDF Viewer")

    with nav_col2:
        st.markdown('<div class="uniform-button">', unsafe_allow_html=True)
        if st.button("View Graph", key="btn_graph", use_container_width=True):
            st.session_state.active_view = "graph"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with nav_col3:
        st.markdown('<div class="uniform-button">', unsafe_allow_html=True)
        if st.button("Extract Text", key="btn_text", use_container_width=True):
            st.session_state.active_view = "text"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with nav_col4:
        st.markdown('<div class="uniform-button">', unsafe_allow_html=True)
        if st.button("View PDF", key="btn_pdf", use_container_width=True):
            st.session_state.active_view = "pdf"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# Main Content
# ------------------------------
with st.container():
    st.divider()
    view = st.session_state.active_view
    pdf_file = st.session_state.get("selected_file")

    if view == "pdf":
        st.subheader("📄 PDF Viewer")
        if pdf_file and os.path.exists(pdf_file):
            try:
                with open(pdf_file, "rb") as f:
                    pdf_bytes = f.read()
                b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="900px" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error displaying PDF: {e}")
        else:
            st.error("No PDF file selected or file does not exist.")
            st.info("Please select a PDF file from the sidebar.")

    elif view == "graph":
        st.subheader("📊 Graph View")
        company_number = st.session_state.get("selected_company_number")
        if pdf_file and os.path.exists(pdf_file) and company_number:
            st.info(f"Generating graph visualization for: {os.path.basename(pdf_file)}")
            # Placeholder for your graph rendering code
            try:
                AZURE_KEY, AZURE_ENDPOINT = load_azure_credentials()
                client = ComputerVisionClient(AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY))
                
                # Define directories
                from_directory = os.path.dirname(pdf_file)
                to_directory = f"{company_number}/filings-json"
                
                # Extract JSON from PDF
                st.info(f"Extracting JSON from: {os.path.basename(pdf_file)}")
                convert_pdf_to_json(client, from_directory, to_directory)
            except:
                pass
        else:
            st.error("No PDF file selected or file does not exist.")

    elif view == "text":
        st.subheader("📝 Extracted Text")
        if pdf_file and os.path.exists(pdf_file):
            st.info(f"Extracting text from: {os.path.basename(pdf_file)}")
            # Placeholder for your text extraction code
        else:
            st.error("No PDF file selected or file does not exist.")

    elif view == "":
        st.subheader("🧾 Extracted JSON")
        if pdf_file and os.path.exists(pdf_file):
            st.info(f"Extracting JSON from: {os.path.basename(pdf_file)}")
            # Placeholder for your JSON extraction code
            st.json({"filename": os.path.basename(pdf_file), "status": "pending extraction"})
        else:
            st.error("No PDF file selected or file does not exist.")