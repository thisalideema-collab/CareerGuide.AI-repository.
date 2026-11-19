
import streamlit as st
from supabase import create_client


def create_auth_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


def register_user(email, password):
    try:
        client = create_auth_client()
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })

        if response.session:
            st.session_state["access_token"] = response.session.access_token
            st.session_state["refresh_token"] = response.session.refresh_token
            st.session_state["user_id"] = str(response.user.id)
            st.session_state["user_email"] = response.user.email
            return "logged_in"

        return "confirmation_required"

    except Exception as e:
        st.error(f"Registration failed: {e}")
        return "error"


def login_user(email, password):
    try:
        client = create_auth_client()
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.session and response.user:
            st.session_state["access_token"] = response.session.access_token
            st.session_state["refresh_token"] = response.session.refresh_token
            st.session_state["user_id"] = str(response.user.id)
            st.session_state["user_email"] = response.user.email
            return True

        return False

    except Exception as e:
        st.error(f"Login failed: {e}")
        return False


def get_user_client():
    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")

    if not access_token or not refresh_token:
        return None

    try:
        client = create_auth_client()
        client.auth.set_session(access_token, refresh_token)
        session = client.auth.get_session()

        if session:
            st.session_state["access_token"] = session.access_token
            st.session_state["refresh_token"] = session.refresh_token

        return client

    except Exception:
        clear_session()
        return None


def clear_session():
    for key in [
        "access_token",
        "refresh_token",
        "user_id",
        "user_email"
    ]:
        st.session_state.pop(key, None)


def logout_user():
    try:
        client = get_user_client()
        if client:
            client.auth.sign_out()
    except Exception:
        pass

    clear_session()
    st.rerun()


def is_authenticated():
    return (
        bool(st.session_state.get("user_id"))
        and bool(st.session_state.get("access_token"))
        and bool(st.session_state.get("refresh_token"))
    )
