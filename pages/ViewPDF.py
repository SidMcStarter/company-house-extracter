import streamlit as st
import base64
import urllib.parse
import os

st.set_page_config(layout="wide")

st.title("Company Files Viewer")

st.write(st.session_state)