
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase_client() -> Client:
    """Create and cache the Supabase connection."""

    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]

        client = create_client(url, key)

        return client

    except Exception as e:
        st.error(f"Supabase configuration error: {e}")
        return None


def test_database_connection():
    """Test access to the programmes table."""

    client = get_supabase_client()

    if client is None:
        return False

    try:
        response = (
            client.table("programmes")
            .select("programme_id", count="exact")
            .limit(1)
            .execute()
        )

        st.success("Supabase connected successfully!")

        st.write(
            f"Available programmes: {response.count}"
        )

        return True

    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return False


def get_all_programmes():
    """Retrieve programme records from Supabase."""

    client = get_supabase_client()

    if client is None:
        return []

    try:
        response = (
            client.table("programmes")
            .select("*")
            .execute()
        )

        return response.data

    except Exception as e:
        st.error(f"Could not retrieve programmes: {e}")
        return []
