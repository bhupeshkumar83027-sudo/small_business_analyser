import streamlit as st
from auth import login_signup_page
from dashboard import dashboard_page

st.set_page_config(page_title="Auth System", page_icon="🔐")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.token = None
    st.session_state.dashboard_data = None

if st.session_state.logged_in:
    dashboard_page()
else:
    login_signup_page()
