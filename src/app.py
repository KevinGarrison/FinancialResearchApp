import streamlit as st
from backend.utils import FinDataFetcher


# --- SESSION STATE SETUP ---
if "tool" not in st.session_state:
    st.session_state.tool = FinDataFetcher()
if "page" not in st.session_state:
    st.session_state.page = "home"  


# --- NAVIGATION CONTROLLER ---
tool = st.session_state.tool

if st.session_state.page == "home":
    tool.show_home()
elif st.session_state.page == "shares":
    tool.show_shares_dashboard()
elif st.session_state.page == "crypto":
    tool.show_crypto_dashboard()
