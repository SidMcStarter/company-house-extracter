from dotenv import load_dotenv
import streamlit as st
import os
import fitz  # PyMuPDF
import urllib.parse
import base64
from api_extracters.search_companies import search_companies
from streamlit_card import card

load_dotenv()

st.set_page_config(layout="wide")
st.title("📄 Company Files Viewer & Uploader")

COMPANY_HOUSE_API_KEY = os.getenv("COMPANY_HOUSE_API_KEY")

company_name = st.text_input("Search for a Company:", key="company_name")
search = st.button("Search")

if search and company_name:
    results = search_companies(company_name, COMPANY_HOUSE_API_KEY=COMPANY_HOUSE_API_KEY)
    if results:
        num_columns = 4
        columns = st.columns(num_columns)
        for idx, result in enumerate(results):
            col = columns[idx % num_columns]
            with col:
                clicked = card(
                    title=result["title"],
                    key=result["company_number"],
                    text=result["company_number"],
                    styles={
                        "card": {
                            "backgroundColor": "#262730",
                            "width": "100%",
                            "border": "1px solid #444",
                            "borderRadius": "10px",
                            "padding": "8px",
                            "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
                        },
                        "text": {
                            "color": "#e0e2e6",
                            "fontSize": "15px",
                        },
                        "title": {
                            "color": "#FF4B4B",
                            "fontSize": "18px",
                            "fontWeight": "bold",
                        }
                    }
                )
    else:
        st.error("No companies found.")

for key, value in st.session_state.items():
    if value is True and key.isnumeric():
        st.session_state["selected_company_number"] = key
        st.switch_page("pages/ViewPDF.py", )
