import streamlit as st
import base64
import urllib.parse
import os
import fitz
from api_extracters.company_house_extracter import download_company_filings
st.set_page_config(layout="wide")

st.title("Company Files Viewer")

COMPANY_HOUSE_API_KEY = os.getenv("COMPANY_HOUSE_API_KEY")
company_number = st.session_state.get("selected_company_number")

if company_number:
    with st.spinner("Loading PDF... This can take a while"):
        # check if the folder exists, if not create it
        folder_path = os.getcwd() + "/" + str(company_number) + "/filings"
        print(f"Folder path: {folder_path}")
        if not os.path.exists(folder_path):
            download_company_filings(company_number, COMPANY_HOUSE_API_KEY)
            st.rerun()
        else:
            files = os.listdir(folder_path)
            cols = st.columns(4)
            for idx, file in enumerate(files):
                if file.endswith(".pdf"):
                    col = cols[idx % 4]
                    with col:
                        file_path = os.path.join(folder_path, file)
                        doc = fitz.open(file_path) #open the pdf
                        page = doc.load_page(0)  # Load the first page
                        pix = page.get_pixmap(dpi=150) #render the page to an iamge
                        img_bytes = pix.tobytes("png")
                        st.image(img_bytes)
                        if st.button(f"Open {file}", key=file):
                            st.session_state["selected_file"] = file_path
                            st.switch_page("pages/ViewPDF.py")
         
                   
            print(f"Files in folder: {files}")
           
else:
    st.error("No company selected. Please select a company from the search results.")
    st.switch_page("Home.py")