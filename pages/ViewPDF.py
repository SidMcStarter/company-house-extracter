import streamlit as st
import base64
import os
import streamlit.components.v1 as components  
from pdf_to_knowledge_final import convert_pdf_to_json, extract_text_from_json, load_azure_credentials, convert_pdf_file_to_json
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from utils.graph_ingest import ingest_text_to_neo4j
from graphs.display_graph import generate_graph_html
from dotenv import load_dotenv
import asyncio
import requests
import time
import io
import json
import fitz  # PyMuPDF
import pathlib


# helper functions
def display_graph_in_streamlit(neo4j_uri=None, neo4j_user=None, neo4j_password=None, company_number=None, file_name=None):
    """Generate and display Neo4j graph in Streamlit"""
    # Generate the graph HTML
    graph_path = f"{company_number}/graphs/{file_name}_graph.html"
    print("GRAPH PATH", graph_path)
    if os.path.exists(graph_path):
        st.info(f"Graph for {company_number} already exists. Displaying the graph.")
    
    else:
        graph_path = generate_graph_html(neo4j_uri, neo4j_user, neo4j_password, company_number, file_name)
    
    # Display the HTML file in Streamlit
    with open(graph_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Use the HTML component to display the graph
    components.html(html_content, height=600)

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
        file_name = os.path.basename(pdf_file).replace('.pdf', '') if pdf_file else "default_graph"
        st.write(f"Displaying graph for company: {company_number} with file name: {file_name}")
        #check if the graph for the company already exists
        path = f"{company_number}/graphs/{file_name}_graph.html"
        
        if os.path.exists(path):
            display_graph_in_streamlit(os.getenv("NEO4J_URI"), os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"), company_number=company_number, file_name=file_name)
        else:
            if pdf_file and os.path.exists(pdf_file) and company_number:
                try:
                    AZURE_KEY, AZURE_ENDPOINT = load_azure_credentials()
                    client = ComputerVisionClient(AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY))
                    
                    # Define directories
                    pdf_file_path = pdf_file
                    to_directory = f"{company_number}/filings-json"
                    
                    to_directory_txt = f"{company_number}/filings-text"
                    text_file_name = os.path.basename(pdf_file).replace('.pdf', '.txt')
                    text_file_path = to_directory_txt + "/" + text_file_name
                    
                    # Extract JSON from PDF
                    with st.spinner(f"Extracting JSON from: {os.path.basename(pdf_file)}"):
                        convert_pdf_file_to_json(client, pdf_file_path, to_directory)
                    
                    if not os.path.exists(text_file_path):
                        st.error(f"Text file not found: {text_file_path}")
                    else:
                        # Process text and display graph
                        with st.spinner(f"Processing text and generating graph..."):
                            asyncio.run(ingest_text_to_neo4j(text_file_path=text_file_path))
                        
                        st.success("Graph generated successfully!")
                        st.write(f"Displaying graph for company: {company_number} with file name: {file_name}")

                        display_graph_in_streamlit(os.getenv("NEO4J_URI"), os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"), company_number=company_number, file_name=file_name)
                        
                except Exception as e:
                    st.error(f"Error generating graph: {str(e)}")
            else:
                st.error("No PDF file selected or company number not provided.")
                if not company_number:
                    st.warning("Please select a company number.")

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
            
