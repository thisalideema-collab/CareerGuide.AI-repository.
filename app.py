
import streamlit as st
import pandas as pd

from src.auth import (
    register_user,
    login_user,
    logout_user,
    is_authenticated,
    get_user_client,
    clear_session
)

from src.student_profile import show_student_profile
from src.database import get_all_programmes
from src.recommendation_page import show_recommendations


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CareerGuide.AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM DESIGN AND CSS
# ============================================================

def load_design():

    st.markdown("""
    <style>

    /* Main application background */

    .stApp {
        background-color: #F7F8FC;
    }

    /* Main content area */

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Sidebar */

    section[data-testid="stSidebar"] {
        background-color: #171A35;
        border-right: 1px solid #25294A;
    }

    section[data-testid="stSidebar"] * {
        color: #F4F5FF !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: transparent;
        border-radius: 9px;
        padding: 9px 12px;
        margin-bottom: 5px;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #30345C;
    }

    /* Headings */

    h1 {
        color: #202447;
        font-weight: 750 !important;
        letter-spacing: -1px;
    }

    h2, h3 {
        color: #292D52;
        font-weight: 650 !important;
    }

    /* Text */

    p {
        color: #555D75;
    }

    /* Buttons */

    .stButton > button,
    .stFormSubmitButton > button {
        background-color: #635BDB;
        color: white !important;
        border: none;
        border-radius: 9px;
        padding: 10px 18px;
        font-weight: 600;
        transition: 0.2s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background-color: #5048C6;
        color: white !important;
        border: none;
    }

    /* Input fields */

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"],
    .stNumberInput input {
        border-radius: 8px;
    }

    /* Cards */

    .cg-card {
        background: white;
        border: 1px solid #E8E9F2;
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 3px 12px rgba(30, 35, 80, 0.04);
        height: 100%;
    }

    .cg-card-title {
        font-size: 14px;
        color: #777D94;
        margin-bottom: 9px;
    }

    .cg-card-value {
        font-size: 30px;
        font-weight: 750;
        color: #282B55;
    }

    .cg-card-description {
        font-size: 12px;
        color: #858BA0;
        margin-top: 5px;
    }

    /* Hero section */

    .cg-hero {
        background: linear-gradient(
            120deg,
            #22264D 0%,
            #4943A1 60%,
            #7668D8 100%
        );
        border-radius: 18px;
        padding: 35px;
        color: white;
        margin-bottom: 25px;
    }

    .cg-hero h1 {
        color: white !important;
        font-size: 34px;
        margin-bottom: 10px;
    }

    .cg-hero p {
        color: #E5E5FF !important;
        font-size: 15px;
    }

    .cg-tag {
        display: inline-block;
        background: rgba(255,255,255,0.16);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        margin-bottom: 12px;
    }

    /* Dividers */

    hr {
        border-color: #E7E8F0;
    }

    /* Login page */

    .login-container {
        max-width: 650px;
        margin: 35px auto 0 auto;
        background: white;
        padding: 32px;
        border-radius: 18px;
        border: 1px solid #E9EAF2;
        box-shadow: 0 8px 30px rgba(30, 35, 80, 0.06);
    }

    /* Footer */

    .cg-footer {
        text-align: center;
        color: #9095A8;
        font-size: 12px;
        padding-top: 30px;
        padding-bottom: 10px;
    }

    </style>
    """, unsafe_allow_html=True)


load_design()


# ============================================================
# REUSABLE UI COMPONENTS
# ============================================================

def show_footer():

    st.markdown("""
    <div class="cg-footer">
        CareerGuide.AI | AI-Based Career and Higher Education Guidance
        <br>
        Sri Lanka | 2026
    </div>
    """, unsafe_allow_html=True)


def metric_card(title, value, description):

    st.markdown(f"""
    <div class="cg-card">
        <div class="cg-card-title">{title}</div>
        <div class="cg-card-value">{value}</div>
        <div class="cg-card-description">{description}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# AUTHENTICATION PAGE
# ============================================================

def authentication_page():

    st.markdown(
        '<div style="text-align:center; padding-top:35px;">'
        '<div style="font-size:48px;">🎓</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<h1 style="text-align:center;">CareerGuide.AI</h1>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p style="text-align:center;">'
        'AI-Based Career and Higher Education Guidance System'
        '</p>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div style="
        text-align:center;
        color:#777D94;
        font-size:14px;
        margin-bottom:20px;
    ">
        Discover suitable Sri Lankan education pathways
        based on your academic background and interests.
    </div>
    """, unsafe_allow_html=True)

    left, center, right = st.columns([1, 2, 1])

    with center:

        login_tab, register_tab = st.tabs([
            "Login",
            "Create Account"
        ])

        # LOGIN

        with login_tab:

            st.subheader("Welcome Back")

            with st.form("login_form"):

                email = st.text_input(
                    "Email Address",
                    placeholder="Enter your email"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password"
                )

                submitted = st.form_submit_button(
                    "Login",
                    use_container_width=True
                )

            if submitted:

                if not email or not password:

                    st.warning("Please complete all fields.")

                else:

                    if login_user(email.strip(), password):

                        st.success("Login successful!")
                        st.rerun()

        # REGISTRATION

        with register_tab:

            st.subheader("Create Your Account")

            with st.form("register_form"):

                email = st.text_input(
                    "Email Address",
                    placeholder="Enter your email",
                    key="new_email"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Minimum 8 characters",
                    key="new_password"
                )

                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password"
                )

                submitted = st.form_submit_button(
                    "Create Account",
                    use_container_width=True
                )

            if submitted:

                if not email or not password or not confirm_password:

                    st.warning("Please complete all fields.")

                elif password != confirm_password:

                    st.error("Passwords do not match.")

                elif len(password) < 8:

                    st.warning(
                        "Password must contain at least 8 characters."
                    )

                else:

                    result = register_user(
                        email.strip(),
                        password
                    )

                    if result == "logged_in":

                        st.success("Account created successfully!")
                        st.rerun()

                    elif result == "confirmation_required":

                        st.success(
                            "Account created successfully. "
                            "Please verify your email before logging in."
                        )

    show_footer()


# ============================================================
# DASHBOARD PAGE
# ============================================================

def dashboard_page():

    st.markdown("""
    <div class="cg-hero">
        <span class="cg-tag">YOUR FUTURE STARTS HERE</span>
        <h1>Welcome to CareerGuide.AI 🎓</h1>
        <p>
            Explore education opportunities, discover your strengths,
            and find pathways towards your future career.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Main metrics

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card(
            "Education Programmes",
            "933",
            "Across Sri Lankan institutions"
        )

    with col2:
        metric_card(
            "Institutions",
            "63",
            "Government, private and vocational"
        )

    with col3:
        metric_card(
            "Education Sectors",
            "3",
            "Multiple learning pathways"
        )

    st.write("")

    st.subheader("Explore CareerGuide.AI")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("""
        <div class="cg-card">
            <div style="font-size:30px;">👨‍🎓</div>
            <h3>Student Profile</h3>
            <p>
                Record your academic background, examination results,
                interests and skills.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="cg-card">
            <div style="font-size:30px;">🎯</div>
            <h3>Career Recommendations</h3>
            <p>
                Discover programmes that match your interests,
                education background and preferences.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    col3, col4 = st.columns(2)

    with col3:

        st.markdown("""
        <div class="cg-card">
            <div style="font-size:30px;">🏛️</div>
            <h3>Programme Explorer</h3>
            <p>
                Explore Sri Lankan universities, institutions,
                qualifications and study opportunities.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col4:

        st.markdown("""
        <div class="cg-card">
            <div style="font-size:30px;">🤖</div>
            <h3>AI Career Assistant</h3>
            <p>
                Get assistance understanding possible career
                and higher education pathways.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    st.info(
        "Getting started: Complete your Student Profile to prepare "
        "for personalised education recommendations."
    )


# ============================================================
# STUDENT PROFILE PAGE
# ============================================================

def student_profile_page(client):

    try:

        show_student_profile(
            client,
            st.session_state["user_id"]
        )

    except Exception as e:

        st.error("Unable to load your student profile.")
        st.exception(e)



# ============================================================
# RECOMMENDATIONS PAGE
# ============================================================

def recommendations_page(client, user_id):

    show_recommendations(
        client,
        user_id
    )


# ============================================================
# PROGRAMME EXPLORER PAGE
# ============================================================

def programme_explorer_page():

    st.title("🏛️ Programme Explorer")

    st.write(
        "Explore higher education programmes available "
        "across Sri Lanka."
    )

    try:

        programmes = get_all_programmes()

        if not programmes:

            st.warning("No programme records could be retrieved.")
            return

        df = pd.DataFrame(programmes)

        st.markdown("### Search and Filter Programmes")

        search = st.text_input(
            "Search by programme, institution, career field or district",
            placeholder="Example: Data Science"
        )

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:

            if "Institution_Type" in df.columns:

                type_column = "Institution_Type"

            elif "institution_type" in df.columns:

                type_column = "institution_type"

            else:

                type_column = None

            if type_column:

                institution_types = sorted(
                    df[type_column].dropna().astype(str).unique().tolist()
                )

                selected_type = st.selectbox(
                    "Institution Type",
                    ["All"] + institution_types
                )

            else:

                selected_type = "All"

        with filter_col2:

            if "District" in df.columns:
                district_column = "District"
            elif "district" in df.columns:
                district_column = "district"
            else:
                district_column = None

            if district_column:

                districts = sorted(
                    df[district_column].dropna().astype(str).unique().tolist()
                )

                selected_district = st.selectbox(
                    "District",
                    ["All"] + districts
                )

            else:

                selected_district = "All"

        with filter_col3:

            if "Qualification_Type" in df.columns:
                qualification_column = "Qualification_Type"
            elif "qualification_type" in df.columns:
                qualification_column = "qualification_type"
            else:
                qualification_column = None

            if qualification_column:

                qualifications = sorted(
                    df[qualification_column]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                selected_qualification = st.selectbox(
                    "Qualification",
                    ["All"] + qualifications
                )

            else:

                selected_qualification = "All"

        # Apply filters

        filtered_df = df.copy()

        if search:

            mask = filtered_df.astype(str).apply(
                lambda column: column.str.contains(
                    search,
                    case=False,
                    na=False,
                    regex=False
                )
            ).any(axis=1)

            filtered_df = filtered_df[mask]

        if selected_type != "All" and type_column:

            filtered_df = filtered_df[
                filtered_df[type_column].astype(str) == selected_type
            ]

        if selected_district != "All" and district_column:

            filtered_df = filtered_df[
                filtered_df[district_column].astype(str) == selected_district
            ]

        if selected_qualification != "All" and qualification_column:

            filtered_df = filtered_df[
                filtered_df[qualification_column].astype(str)
                == selected_qualification
            ]

        st.divider()

        st.metric(
            "Matching Programmes",
            len(filtered_df)
        )

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:

        st.error("Unable to retrieve programmes.")
        st.exception(e)


# ============================================================
# AI CAREER ASSISTANT PAGE
# ============================================================

def career_assistant_page():

    st.title("🤖 AI Career Assistant")

    st.write(
        "Get guidance about education opportunities, "
        "career fields and higher education pathways."
    )

    st.markdown("""
    <div class="cg-card">
        <h3>Career Guidance Assistant</h3>
        <p>
            The AI assistant will help students understand
            their possible education and career pathways.
        </p>
        <p>
            It will use the programme database to provide
            grounded information about Sri Lankan institutions
            and available qualifications.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.info(
        "Llama integration is planned for a later development stage. "
        "The assistant is not yet connected to an AI model."
    )


# ============================================================
# MAIN APPLICATION DASHBOARD
# ============================================================

def application_dashboard():

    client = get_user_client()

    if client is None:

        clear_session()

        st.warning(
            "Your login session has expired. Please log in again."
        )

        st.rerun()

    # SIDEBAR BRANDING

    st.sidebar.markdown("""
    <div style="padding: 15px 0 8px 0;">
        <div style="font-size:28px; font-weight:750;">
            🎓 CareerGuide.AI
        </div>
        <div style="font-size:12px; opacity:0.8;">
            Your Education Pathway Assistant
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.divider()

    st.sidebar.markdown("**ACCOUNT**")

    st.sidebar.write(
        st.session_state.get("user_email", "")
    )

    st.sidebar.divider()

    # SINGLE NAVIGATION MENU

    st.sidebar.markdown("**MAIN MENU**")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Student Profile",
            "Recommendations",
            "Programme Explorer",
            "AI Career Assistant"
        ],
        label_visibility="collapsed"
    )

    st.sidebar.divider()

    st.sidebar.markdown("""
    <div style="font-size:12px; opacity:0.75;">
        CAREERGUIDE.AI<br>
        Sri Lanka | 2026
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button(
        "Logout",
        use_container_width=True
    ):

        logout_user()

   
    # PAGE ROUTING

    if page == "Dashboard":

        dashboard_page()

    elif page == "Student Profile":

        student_profile_page(client)

    elif page == "Recommendations":

        recommendations_page(
            client,
            st.session_state["user_id"]
        )

    elif page == "Programme Explorer":

        programme_explorer_page()

    elif page == "AI Career Assistant":

        career_assistant_page()

    show_footer()

# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if is_authenticated():

    application_dashboard()

else:

    authentication_page()

