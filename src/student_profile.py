
import streamlit as st


# ============================================================
# OPTIONS
# ============================================================

OL_SUBJECTS = [
    "Buddhism",
    "Catholicism",
    "Christianity",
    "Islam",
    "Hinduism",
    "Sinhala Language and Literature",
    "Tamil Language and Literature",
    "English Language",
    "Mathematics",
    "Science",
    "History",
    "Business and Accounting Studies",
    "Geography",
    "Civic Education",
    "Entrepreneurship Studies",
    "Second Language - Sinhala",
    "Second Language - Tamil",
    "Art",
    "Music",
    "Dancing",
    "Drama and Theatre",
    "ICT",
    "Agriculture and Food Technology",
    "Health and Physical Education",
    "Other"
]

AL_SUBJECTS = [
    "Biology",
    "Physics",
    "Chemistry",
    "Combined Mathematics",
    "Agricultural Science",
    "Information and Communication Technology",
    "Business Studies",
    "Accounting",
    "Economics",
    "Business Statistics",
    "Logic and Scientific Method",
    "Political Science",
    "Geography",
    "History",
    "Communication and Media Studies",
    "Sinhala",
    "Tamil",
    "English",
    "Buddhist Civilization",
    "Christian Civilization",
    "Hindu Civilization",
    "Islamic Civilization",
    "Dancing",
    "Art",
    "Music",
    "Drama and Theatre",
    "Engineering Technology",
    "Science for Technology",
    "Bio Systems Technology",
    "Other"
]

OL_GRADES = ["A", "B", "C", "S", "W"]

AL_GRADES = ["A", "B", "C", "S", "F", "W"]

INTEREST_OPTIONS = [
    "Information Technology",
    "Data Science",
    "Artificial Intelligence",
    "Software Engineering",
    "Computer Science",
    "Business Management",
    "Accounting and Finance",
    "Banking",
    "Economics",
    "Engineering",
    "Medicine",
    "Nursing",
    "Pharmacy",
    "Biological Science",
    "Physical Science",
    "Agriculture",
    "Technology",
    "Education and Teaching",
    "Law",
    "Psychology",
    "Arts and Humanities",
    "Media and Communication",
    "Design and Creativity",
    "Hospitality and Tourism",
    "Construction",
    "Automobile Technology",
    "Entrepreneurship",
    "Social Sciences",
    "Environmental Science"
]

SKILL_OPTIONS = [
    "Python Programming",
    "Java Programming",
    "C Programming",
    "SQL and Database Management",
    "Web Development",
    "Data Analysis",
    "Machine Learning",
    "Microsoft Excel",
    "Microsoft Office",
    "Communication",
    "Teamwork",
    "Leadership",
    "Problem Solving",
    "Critical Thinking",
    "Creativity",
    "Time Management",
    "Research Skills",
    "Presentation Skills",
    "Financial Management",
    "Accounting",
    "Graphic Design",
    "Digital Marketing",
    "Project Management",
    "Customer Service",
    "Language Skills"
]

DISTRICTS = [
    "Ampara",
    "Anuradhapura",
    "Badulla",
    "Batticaloa",
    "Colombo",
    "Galle",
    "Gampaha",
    "Hambantota",
    "Jaffna",
    "Kalutara",
    "Kandy",
    "Kegalle",
    "Kilinochchi",
    "Kurunegala",
    "Mannar",
    "Matale",
    "Matara",
    "Monaragala",
    "Mullaitivu",
    "Nuwara Eliya",
    "Polonnaruwa",
    "Puttalam",
    "Ratnapura",
    "Trincomalee",
    "Vavuniya"
]

STREAMS = [
    "Biological Science",
    "Physical Science",
    "Commerce",
    "Arts",
    "Technology",
    "Other"
]

EDUCATION_STAGES = [
    "Completed O/L",
    "Completed A/L",
    "Currently Studying A/L",
    "Other"
]

EDUCATION_PREFERENCES = [
    "Degree",
    "Diploma",
    "Higher Diploma",
    "Certificate",
    "Vocational Training",
    "Any"
]

# Monthly budget options.
# Values represent the conservative lower boundary of each range.
BUDGET_OPTIONS = {
    "Below LKR 50,000": 49999,
    "LKR 50,000 - 100,000": 50000,
    "LKR 100,000 - 200,000": 100000,
    "LKR 200,000 - 300,000": 200000,
    "Above LKR 300,000": 300001
}

YEARS = [""] + list(range(2026, 1999, -1))

EMPTY = "— Select —"


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_profile(client, user_id):

    response = (
        client.table("student_profiles")
        .select("*")
        .eq("auth_user_id", user_id)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


def get_student_records(client, table_name, student_id):

    response = (
        client.table(table_name)
        .select("*")
        .eq("student_id", student_id)
        .execute()
    )

    return response.data or []


def selected_index(options, value):

    if value in options:
        return options.index(value)

    return 0


def save_academic_records(client, student_id, rows):

    client.table("student_academic_records").delete().eq(
        "student_id", student_id
    ).execute()

    if rows:
        client.table("student_academic_records").insert(rows).execute()


def save_multiple_choices(
    client, table_name, column_name, student_id, values
):

    client.table(table_name).delete().eq(
        "student_id", student_id
    ).execute()

    if values:

        rows = [
            {
                "student_id": student_id,
                column_name: value
            }
            for value in values
        ]

        client.table(table_name).insert(rows).execute()


# ============================================================
# STUDENT PROFILE PAGE
# ============================================================

def show_student_profile(client, user_id):

    st.title("🎓 Student Profile")

    st.write(
        "Complete your academic background, interests, "
        "skills and education preferences."
    )

    st.info(
        "Your information is securely associated with your "
        "registered CareerGuide.AI account."
    )

    # --------------------------------------------------------
    # LOAD EXISTING INFORMATION
    # --------------------------------------------------------

    try:

        profile = get_profile(client, user_id)

        student_id = (
            profile.get("student_id")
            if profile else None
        )

        academic_records = []
        existing_interests = []
        existing_skills = []

        if student_id:

            academic_records = get_student_records(
                client,
                "student_academic_records",
                student_id
            )

            interest_records = get_student_records(
                client,
                "student_interests",
                student_id
            )

            skill_records = get_student_records(
                client,
                "student_skills",
                student_id
            )

            existing_interests = [
                item["interest_name"]
                for item in interest_records
            ]

            existing_skills = [
                item["skill_name"]
                for item in skill_records
            ]

    except Exception as e:

        st.error(f"Could not load your profile: {e}")
        return

    ol_records = [
        r for r in academic_records
        if r.get("qualification") == "O/L"
    ]

    al_records = [
        r for r in academic_records
        if r.get("qualification") == "A/L"
    ]

    # --------------------------------------------------------
    # EXISTING RECORD LOOKUP
    # --------------------------------------------------------

    def get_existing_subject(records, row_number):

        if row_number < len(records):
            return records[row_number].get("subject") or ""

        return ""


    def get_existing_grade(records, row_number):

        if row_number < len(records):
            return records[row_number].get("grade") or ""

        return ""


    def get_existing_year(records):

        if records and records[0].get("examination_year"):
            return records[0]["examination_year"]

        return ""


    # --------------------------------------------------------
    # SECTION 1 - PERSONAL INFORMATION
    # --------------------------------------------------------

    st.divider()
    st.header("1. Personal and Education Information")

    col1, col2 = st.columns(2)

    with col1:

        current_district = (
            profile.get("district", "")
            if profile else ""
        )

        district = st.selectbox(
            "District",
            [EMPTY] + DISTRICTS,
            index=selected_index(
                [EMPTY] + DISTRICTS,
                current_district
            )
        )

    with col2:

        current_stage = (
            profile.get("education_stage", "")
            if profile else ""
        )

        education_stage = st.selectbox(
            "Current Education Stage",
            [EMPTY] + EDUCATION_STAGES,
            index=selected_index(
                [EMPTY] + EDUCATION_STAGES,
                current_stage
            )
        )


    # --------------------------------------------------------
    # SECTION 2 - O/L RESULTS
    # --------------------------------------------------------

    st.divider()
    st.header("2. G.C.E. Ordinary Level Results")

    st.caption(
        "Select your examination subjects and corresponding grades. "
        "Leave unused rows blank."
    )

    ol_year_default = get_existing_year(ol_records)

    ol_year = st.selectbox(
        "O/L Examination Year",
        YEARS,
        index=selected_index(YEARS, ol_year_default),
        format_func=lambda x: "Select year" if x == "" else str(x)
    )

    ol_subjects_entered = []

    for i in range(9):

        col1, col2 = st.columns([3, 1])

        old_subject = get_existing_subject(ol_records, i)
        old_grade = get_existing_grade(ol_records, i)

        with col1:

            subject = st.selectbox(
                f"O/L Subject {i + 1}",
                [EMPTY] + OL_SUBJECTS,
                index=selected_index(
                    [EMPTY] + OL_SUBJECTS,
                    old_subject
                ),
                key=f"ol_subject_{i}"
            )

        with col2:

            grade = st.selectbox(
                f"Grade {i + 1}",
                [EMPTY] + OL_GRADES,
                index=selected_index(
                    [EMPTY] + OL_GRADES,
                    old_grade
                ),
                key=f"ol_grade_{i}"
            )

        ol_subjects_entered.append((subject, grade))


    # --------------------------------------------------------
    # SECTION 3 - A/L RESULTS
    # --------------------------------------------------------

    st.divider()
    st.header("3. G.C.E. Advanced Level Results")

    st.caption(
        "Select your A/L stream, examination year, subjects and grades."
    )

    current_stream = next(
        (
            r.get("stream")
            for r in al_records
            if r.get("stream")
        ),
        ""
    )

    al_stream = st.selectbox(
        "A/L Stream",
        [EMPTY] + STREAMS,
        index=selected_index(
            [EMPTY] + STREAMS,
            current_stream
        )
    )

    al_year_default = get_existing_year(al_records)

    al_year = st.selectbox(
        "A/L Examination Year",
        YEARS,
        index=selected_index(YEARS, al_year_default),
        format_func=lambda x: "Select year" if x == "" else str(x)
    )

    al_subjects_entered = []

    for i in range(3):

        col1, col2 = st.columns([3, 1])

        old_subject = get_existing_subject(al_records, i)
        old_grade = get_existing_grade(al_records, i)

        with col1:

            subject = st.selectbox(
                f"A/L Subject {i + 1}",
                [EMPTY] + AL_SUBJECTS,
                index=selected_index(
                    [EMPTY] + AL_SUBJECTS,
                    old_subject
                ),
                key=f"al_subject_{i}"
            )

        with col2:

            grade = st.selectbox(
                f"Grade {i + 1}",
                [EMPTY] + AL_GRADES,
                index=selected_index(
                    [EMPTY] + AL_GRADES,
                    old_grade
                ),
                key=f"al_grade_{i}"
            )

        al_subjects_entered.append((subject, grade))


    # --------------------------------------------------------
    # SECTION 4 - INTERESTS
    # --------------------------------------------------------

    st.divider()
    st.header("4. Student Interests")

    st.caption("Select up to three areas that interest you.")

    interests = st.multiselect(
        "Choose your interests",
        options=INTEREST_OPTIONS,
        default=[
            x for x in existing_interests
            if x in INTEREST_OPTIONS
        ],
        max_selections=3,
        placeholder="Select your interests..."
    )


    # --------------------------------------------------------
    # SECTION 5 - SKILLS
    # --------------------------------------------------------

    st.divider()
    st.header("5. Skills")

    st.caption(
        "Select the skills you currently have. "
        "You can choose multiple options."
    )

    skills = st.multiselect(
        "Choose your skills",
        options=SKILL_OPTIONS,
        default=[
            x for x in existing_skills
            if x in SKILL_OPTIONS
        ],
        placeholder="Select your skills..."
    )


    # --------------------------------------------------------
    # SECTION 6 - EDUCATION PREFERENCES
    # --------------------------------------------------------

    st.divider()
    st.header("6. Education Preferences")

    col1, col2 = st.columns(2)

    with col1:

        current_preference = (
            profile.get("education_preference", "")
            if profile else ""
        )

        education_preference = st.selectbox(
            "Preferred Qualification",
            [EMPTY] + EDUCATION_PREFERENCES,
            index=selected_index(
                [EMPTY] + EDUCATION_PREFERENCES,
                current_preference
            )
        )

    with col2:

        # Read the previously saved monthly budget.
        current_budget_value = (
            str(profile.get("budget_category") or "").strip()
            if profile else ""
        )

        # Convert the saved numeric value back to its dropdown range.
        default_budget = EMPTY

        if current_budget_value.replace(",", "").isdigit():

            saved_budget = int(
                current_budget_value.replace(",", "")
            )

            if saved_budget < 50000:
                default_budget = "Below LKR 50,000"

            elif saved_budget < 100000:
                default_budget = "LKR 50,000 - 100,000"

            elif saved_budget < 200000:
                default_budget = "LKR 100,000 - 200,000"

            elif saved_budget <= 300000:
                default_budget = "LKR 200,000 - 300,000"

            else:
                default_budget = "Above LKR 300,000"

        budget_labels = list(BUDGET_OPTIONS.keys())

        budget_category = st.selectbox(
            "Monthly Education Budget (LKR)",
            [EMPTY] + budget_labels,
            index=selected_index(
                [EMPTY] + budget_labels,
                default_budget
            )
        )


    # --------------------------------------------------------
    # SAVE BUTTON
    # --------------------------------------------------------

    st.divider()

    save_button = st.button(
        "💾 Save Student Profile",
        type="primary",
        use_container_width=True
    )


    # --------------------------------------------------------
    # SAVE AND VALIDATE
    # --------------------------------------------------------

    if save_button:

        try:

            # Validate required profile information.

            if district == EMPTY:
                st.error("Please select your district.")
                return

            if education_stage == EMPTY:
                st.error("Please select your education stage.")
                return

            if education_preference == EMPTY:
                st.error("Please select your preferred qualification.")
                return

            if budget_category == EMPTY:
                st.error(
                    "Please select your monthly education budget."
                )
                return

            # Convert the selected budget range into a numeric value.
            monthly_budget = BUDGET_OPTIONS[budget_category]


            # ------------------------------------------------
            # VALIDATE O/L SUBJECT-GRADE COMBINATIONS
            # ------------------------------------------------

            ol_rows = []

            for subject, grade in ol_subjects_entered:

                if subject == EMPTY and grade != EMPTY:
                    st.error(
                        "Select an O/L subject for every chosen grade."
                    )
                    return

                if subject != EMPTY and grade == EMPTY:
                    st.error(
                        f"Please select the grade for {subject}."
                    )
                    return

                if subject != EMPTY:

                    ol_rows.append({
                        "student_id": None,
                        "qualification": "O/L",
                        "subject": subject,
                        "grade": grade,
                        "stream": None,
                        "examination_year": (
                            int(ol_year) if ol_year else None
                        )
                    })


            # ------------------------------------------------
            # VALIDATE A/L SUBJECT-GRADE COMBINATIONS
            # ------------------------------------------------

            al_rows = []

            for subject, grade in al_subjects_entered:

                if subject == EMPTY and grade != EMPTY:
                    st.error(
                        "Select an A/L subject for every chosen grade."
                    )
                    return

                if subject != EMPTY and grade == EMPTY:
                    st.error(
                        f"Please select the grade for {subject}."
                    )
                    return

                if subject != EMPTY:

                    al_rows.append({
                        "student_id": None,
                        "qualification": "A/L",
                        "subject": subject,
                        "grade": grade,
                        "stream": (
                            al_stream
                            if al_stream != EMPTY
                            else None
                        ),
                        "examination_year": (
                            int(al_year) if al_year else None
                        )
                    })


            # Check for duplicate subjects.

            ol_names = [r["subject"] for r in ol_rows]
            al_names = [r["subject"] for r in al_rows]

            if len(ol_names) != len(set(ol_names)):
                st.error("Please remove duplicate O/L subjects.")
                return

            if len(al_names) != len(set(al_names)):
                st.error("Please remove duplicate A/L subjects.")
                return

            if al_rows and al_stream == EMPTY:
                st.error("Please select your A/L stream.")
                return

            if (
                education_stage == "Completed A/L"
                and not al_rows
            ):
                st.error(
                    "Please enter your A/L subjects and grades."
                )
                return

            if (
                education_stage == "Currently Studying A/L"
                and not al_rows
            ):
                st.error(
                    "Please enter your current A/L subjects."
                )
                return


            # ------------------------------------------------
            # PREPARE PROFILE RECORD
            # ------------------------------------------------

            profile_data = {
                "auth_user_id": user_id,
                "district": district,
                "education_stage": education_stage,
                "education_preference": education_preference,
                "budget_category": str(monthly_budget)
            }


            # ------------------------------------------------
            # INSERT OR UPDATE STUDENT PROFILE
            # ------------------------------------------------

            saved_profile = (
                client.table("student_profiles")
                .upsert(
                    profile_data,
                    on_conflict="auth_user_id"
                )
                .select("student_id")
                .execute()
            )

            if not saved_profile.data:
                raise Exception(
                    "Student profile was not returned."
                )

            student_id = saved_profile.data[0]["student_id"]


            # ------------------------------------------------
            # SAVE ACADEMIC RECORDS
            # ------------------------------------------------

            academic_rows = ol_rows + al_rows

            for record in academic_rows:
                record["student_id"] = student_id

            save_academic_records(
                client,
                student_id,
                academic_rows
            )


            # ------------------------------------------------
            # SAVE INTERESTS
            # ------------------------------------------------

            save_multiple_choices(
                client,
                "student_interests",
                "interest_name",
                student_id,
                interests
            )


            # ------------------------------------------------
            # SAVE SKILLS
            # ------------------------------------------------

            save_multiple_choices(
                client,
                "student_skills",
                "skill_name",
                student_id,
                skills
            )


            # ------------------------------------------------
            # SUCCESS MESSAGE
            # ------------------------------------------------

            st.success(
                "Your student profile has been saved successfully!"
            )

            st.info(f"Your Student ID is {student_id}.")

            st.balloons()


        except Exception as e:

            st.error(
                f"Unable to save your student profile: {e}"
            )

