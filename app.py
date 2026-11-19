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
from src.ai_assistant import show_ai_assistant


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

    /* Paragraphs */

    p {
        color: #555D75;
    }

    /* Buttons - Improved Visibility */

    .stButton > button,
    .stFormSubmitButton > button,
    .stDownloadButton > button,
    .stLinkButton > a {

        background-color: #635BDB !important;

        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;

        border: 1px solid #635BDB !important;
        border-radius: 9px;

        padding: 10px 18px;

        font-weight: 700 !important;

        transition: 0.2s ease;
    }

    /* Force nested button text to remain white */

    .stButton > button *,
    .stFormSubmitButton > button *,
    .stDownloadButton > button *,
    .stLinkButton > a * {

        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Button hover */

    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    .stDownloadButton > button:hover,
    .stLinkButton > a:hover {

        background-color: #5048C6 !important;

        border-color: #5048C6 !important;

        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Disabled buttons */

    .stButton > button:disabled,
    .stFormSubmitButton > button:disabled {

        background-color: #7770DF !important;

        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;

        opacity: 1 !important;
    }

    /* Input fields */

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"],
    .stNumberInput input {
        border-radius: 8px;
    }

    /* Dashboard cards */

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
        "Explore higher education programmes offered by "
        "government, private and vocational institutions in Sri Lanka."
    )

    try:

        programmes = get_all_programmes()

        if not programmes:

            st.warning(
                "No programme records are currently available."
            )

            return

        df = pd.DataFrame(programmes)

        if df.empty:

            st.warning("No programme records are available.")

            return

        # --------------------------------------------------
        # HELPER FUNCTIONS
        # --------------------------------------------------

        def normalise(value):

            if value is None:
                return ""

            return str(value).strip()

        def get_value(row, *possible_names):

            for name in possible_names:

                if name in row.index:

                    value = row[name]

                    if pd.notna(value) and str(value).strip():

                        return value

            return None

        def get_filter_column(*possible_names):

            for name in possible_names:

                if name in df.columns:

                    return name

            return None

        def filter_options(column):

            if not column:
                return ["All"]

            values = (
                df[column]
                .dropna()
                .astype(str)
                .str.strip()
            )

            values = sorted(
                value for value in values.unique()
                if value
            )

            return ["All"] + values

        def format_value(value):

            if value is None or pd.isna(value):

                return "Not available"

            return str(value).strip()

        # --------------------------------------------------
        # SEARCH
        # --------------------------------------------------

        st.subheader("Search and Filter Programmes")

        search_text = st.text_input(
            "Search programmes",
            placeholder=(
                "Search programme, institution, career field or district..."
            )
        )

        # --------------------------------------------------
        # FILTER COLUMNS
        # --------------------------------------------------

        institution_col = get_filter_column(
            "institution_type", "Institution_Type"
        )

        district_col = get_filter_column(
            "district", "District"
        )

        qualification_col = get_filter_column(
            "qualification_type", "Qualification_Type"
        )

        career_col = get_filter_column(
            "career_field", "Career_Field"
        )

        study_mode_col = get_filter_column(
            "study_mode", "Study_Mode"
        )

        # --------------------------------------------------
        # FILTERS
        # --------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            institution_filter = st.selectbox(
                "Institution Type",
                filter_options(institution_col),
                key="explorer_institution"
            )

        with col2:

            district_filter = st.selectbox(
                "District",
                filter_options(district_col),
                key="explorer_district"
            )

        with col3:

            qualification_filter = st.selectbox(
                "Qualification",
                filter_options(qualification_col),
                key="explorer_qualification"
            )

        col4, col5 = st.columns(2)

        with col4:

            career_filter = st.selectbox(
                "Career Field",
                filter_options(career_col),
                key="explorer_career"
            )

        with col5:

            study_mode_filter = st.selectbox(
                "Study Mode",
                filter_options(study_mode_col),
                key="explorer_study_mode"
            )

        # --------------------------------------------------
        # APPLY FILTERS
        # --------------------------------------------------

        filtered_df = df.copy()

        filter_conditions = [
            (institution_col, institution_filter),
            (district_col, district_filter),
            (qualification_col, qualification_filter),
            (career_col, career_filter),
            (study_mode_col, study_mode_filter)
        ]

        for column, selected_value in filter_conditions:

            if column and selected_value != "All":

                filtered_df = filtered_df[
                    filtered_df[column]
                    .astype(str)
                    .str.strip()
                    == selected_value
                ]

        # --------------------------------------------------
        # SEARCH ACROSS RELEVANT FIELDS
        # --------------------------------------------------

        if search_text.strip():

            search_columns = [
                "programme_name", "Programme_Name",
                "institution_name", "Institution_Name",
                "career_field", "Career_Field",
                "district", "District",
                "faculty", "Faculty",
                "entry_requirements", "Entry_Requirements"
            ]

            available_search_columns = [
                column for column in search_columns
                if column in filtered_df.columns
            ]

            if available_search_columns:

                search_mask = filtered_df[
                    available_search_columns
                ].fillna("").astype(str).apply(
                    lambda column: column.str.contains(
                        search_text.strip(),
                        case=False,
                        regex=False
                    )
                ).any(axis=1)

                filtered_df = filtered_df[search_mask]

        # --------------------------------------------------
        # RESULTS SUMMARY
        # --------------------------------------------------

        st.divider()

        st.metric(
            "Matching Programmes",
            len(filtered_df)
        )

        if filtered_df.empty:

            st.info(
                "No programmes match your search. "
                "Try changing your filters."
            )

            return

        # --------------------------------------------------
        # PAGINATION
        # --------------------------------------------------

        results_per_page = st.selectbox(
            "Results per page",
            [6, 12, 18, 24],
            index=1,
            key="explorer_results_per_page"
        )

        total_results = len(filtered_df)

        total_pages = (
            total_results + results_per_page - 1
        ) // results_per_page

        current_page = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key="explorer_page_number"
        )

        start_index = (current_page - 1) * results_per_page

        end_index = start_index + results_per_page

        page_df = filtered_df.iloc[start_index:end_index]

        st.caption(
            f"Showing {start_index + 1}–"
            f"{min(end_index, total_results)} "
            f"of {total_results} programmes | "
            f"Page {current_page} of {total_pages}"
        )

        # --------------------------------------------------
        # DISPLAY PROGRAMME CARDS
        # --------------------------------------------------

        for _, programme in page_df.iterrows():

            programme_name = format_value(
                get_value(
                    programme,
                    "programme_name", "Programme_Name"
                )
            )

            institution_name = format_value(
                get_value(
                    programme,
                    "institution_name", "Institution_Name"
                )
            )

            institution_type = format_value(
                get_value(
                    programme,
                    "institution_type", "Institution_Type"
                )
            )

            qualification = format_value(
                get_value(
                    programme,
                    "qualification_type", "Qualification_Type"
                )
            )

            career_field = format_value(
                get_value(
                    programme,
                    "career_field", "Career_Field"
                )
            )

            duration = format_value(
                get_value(
                    programme,
                    "duration", "Duration"
                )
            )

            study_mode = format_value(
                get_value(
                    programme,
                    "study_mode", "Study_Mode"
                )
            )

            location = format_value(
                get_value(
                    programme,
                    "location", "Location"
                )
            )

            district = format_value(
                get_value(
                    programme,
                    "district", "District"
                )
            )

            fee = get_value(
                programme,
                "total_tuition_fee", "Total_Tuition_Fee"
            )

            currency = get_value(
                programme,
                "fee_currency", "Fee_Currency"
            )

            fee_status = normalise(
                get_value(
                    programme,
                    "fee_status", "Fee_Status"
                )
            )

            entry_requirements = format_value(
                get_value(
                    programme,
                    "entry_requirements", "Entry_Requirements"
                )
            )

            required_stream = format_value(
                get_value(
                    programme,
                    "required_al_stream", "Required_AL_Stream"
                )
            )

            required_subjects = format_value(
                get_value(
                    programme,
                    "required_al_subjects", "Required_AL_Subjects"
                )
            )

            official_url = normalise(
                get_value(
                    programme,
                    "official_url", "Official_URL"
                )
            )

            # Fee display
            # Missing fee information is never treated as free.

            if "free" in fee_status.lower():

                fee_display = "Listed as Free"

            elif fee is not None:

                fee_display = (
                    f"{currency} {fee}"
                    if currency
                    else str(fee)
                )

            elif fee_status:

                fee_display = fee_status

            else:

                fee_display = "Not available"

            # --------------------------------------------------
            # PROGRAMME CARD
            # --------------------------------------------------

            with st.container(border=True):

                st.subheader(programme_name)

                st.markdown(
                    f"**Institution:** {institution_name}"
                )

                st.caption(
                    f"{institution_type} | {career_field}"
                )

                info1, info2, info3 = st.columns(3)

                with info1:

                    st.markdown("**Qualification**")
                    st.write(qualification)

                with info2:

                    st.markdown("**Duration**")
                    st.write(duration)

                with info3:

                    st.markdown("**Study Mode**")
                    st.write(study_mode)

                info4, info5 = st.columns(2)

                with info4:

                    st.markdown("**Location**")

                    if (
                        location != "Not available"
                        and district != "Not available"
                    ):

                        st.write(f"{location}, {district}")

                    elif location != "Not available":

                        st.write(location)

                    else:

                        st.write(district)

                with info5:

                    st.markdown("**Tuition Fee Information**")
                    st.write(fee_display)

                with st.expander("View Programme Details"):

                    st.markdown("**Entry Requirements**")
                    st.write(entry_requirements)

                    st.markdown("**Required A/L Stream**")
                    st.write(required_stream)

                    st.markdown("**Required A/L Subjects**")
                    st.write(required_subjects)

                    st.markdown("**Fee Status**")

                    st.write(
                        fee_status if fee_status
                        else "Not available"
                    )

                    if (
                        official_url.startswith("https://")
                        or official_url.startswith("http://")
                    ):

                        st.link_button(
                            "Visit Official Website",
                            official_url
                        )

                    else:

                        st.caption(
                            "Official website link not available."
                        )

    except Exception as e:

        st.error("Unable to load the Programme Explorer.")

        st.exception(e)


# ============================================================
# AI CAREER ASSISTANT PAGE
# ============================================================

def career_assistant_page():

    show_ai_assistant()


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
        st.rerun()

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

