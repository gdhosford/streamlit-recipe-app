# db.py
import psycopg2
import psycopg2.extras
import streamlit as st

def get_connection():
    """Returns a new PostgreSQL connection using the URL stored in st.secrets."""
    return psycopg2.connect(st.secrets["DB_URL"])