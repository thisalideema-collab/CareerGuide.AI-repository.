
import streamlit as st

from src.database import test_database_connection

st.set_page_config(
    page_title="CareerGuide.AI",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 CareerGuide.AI")

st.subheader(
    "AI-Based Career and Higher Education Guidance System"
)

st.write(
    "Welcome to CareerGuide.AI. "
    "Discover suitable education pathways "
    "based on your academic background and interests."
)

st.divider()

st.header("Database Connection Test")

if st.button("Test Supabase Connection"):
    test_database_connection()
