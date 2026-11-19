import streamlit as st
import pandas as pd
from groq import Groq

from src.recommender import recommend_programmes
from src.xai_explainer import explain_recommendation
from src.financial_assessment import (
    assess_financial_status,
    assess_academic_status
)


# ============================================================
# 1. HELPER FUNCTIONS
# ============================================================

def find_column(df, names):
    """Find a dataframe column without case sensitivity."""
    columns = {
        str(column).strip().lower().replace(" ", "_"): column
        for column in df.columns
    }

    for name in names:
        key = name.strip().lower().replace(" ", "_")
        if key in columns:
            return columns[key]

    return None


def safe_value(row, column, fallback="Not available"):
    """Safely retrieve a value from a pandas row."""
    if not column:
        return fallback

    value = row.get(column, fallback)

    if value is None:
        return fallback

    try:
        if pd.isna(value):
            return fallback
    except (TypeError, ValueError):
        pass

    return value


def display_value(value, fallback="Not available"):
    """Format a value for student-facing display."""
    if value is None:
        return fallback

    try:
        if pd.isna(value):
            return fallback
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "null"}:
        return fallback

    return text


def valid_url(value):
    """Accept only HTTP or HTTPS official website links."""
    url = display_value(value, "")

    if url.startswith(("https://", "http://")):
        return url

    return None


# ============================================================
# 2. LOAD STUDENT PROFILE FROM SUPABASE
# ============================================================

def load_student_data(client, user_id):
    """
    Load the logged-in student's profile and related records.

    IMPORTANT:
    The Supabase client is passed into this function explicitly.
    It is never read from an undefined global variable.
    """
    if client is None:
        raise ValueError("Supabase client is not available.")

    if not user_id:
        raise ValueError("Authenticated user ID is missing.")

    profile_response = (
        client.table("student_profiles")
        .select("*")
        .eq("auth_user_id", user_id)
        .limit(1)
        .execute()
    )

    if not profile_response.data:
        return None

    profile = profile_response.data[0]
    student_id = profile.get("student_id")

    if not student_id:
        raise ValueError(
            "The student profile does not contain a student_id."
        )

    academic = (
        client.table("student_academic_records")
        .select("*")
        .eq("student_id", student_id)
        .execute()
    ).data or []

    interests = (
        client.table("student_interests")
        .select("interest_name")
        .eq("student_id", student_id)
        .execute()
    ).data or []

    skills = (
        client.table("student_skills")
        .select("skill_name")
        .eq("student_id", student_id)
        .execute()
    ).data or []

    # The trained recommendation model uses these four profile fields.
    streams = [
        record.get("stream")
        for record in academic
        if (
            str(record.get("qualification", "")).strip().upper() == "A/L"
            and record.get("stream")
        )
    ]

    model_input = {
        "Student_Stage": profile.get("education_stage") or "",
        "AL_Stream": streams[0] if streams else "",
        "Interests_Select_Up_to_3": ", ".join(
            str(record.get("interest_name", "")).strip()
            for record in interests
            if record.get("interest_name")
        ),
        "Education_Preference": profile.get(
            "education_preference"
        ) or ""
    }

    return {
        "profile": profile,
        "academic": academic,
        "interests": interests,
        "skills": skills,
        "model_input": model_input
    }


# ============================================================
# 3. DISPLAY STUDENT PROFILE SUMMARY
# ============================================================

def display_student_summary(student, monthly_budget):

    profile = student["profile"]

    st.subheader("Your Profile Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Education Stage",
        profile.get("education_stage") or "Not specified"
    )

    col2.metric(
        "Selected Interests",
        len(student["interests"])
    )

    col3.metric(
        "Monthly Budget",
        f"LKR {monthly_budget:,.0f}"
        if monthly_budget is not None
        else "Not provided"
    )

    with st.expander("View saved student information"):

        st.write("**District**")
        st.write(profile.get("district") or "Not specified")

        st.write("**Preferred Qualification**")
        st.write(
            profile.get("education_preference") or "Not specified"
        )

        st.write("**Interests**")
        st.write(
            ", ".join(
                record.get("interest_name", "")
                for record in student["interests"]
                if record.get("interest_name")
            ) or "None recorded"
        )

        st.write("**Skills**")
        st.write(
            ", ".join(
                record.get("skill_name", "")
                for record in student["skills"]
                if record.get("skill_name")
            ) or "None recorded"
        )

        st.write("**Academic Records**")

        if student["academic"]:
            academic_df = pd.DataFrame(student["academic"])

            preferred_columns = [
                "qualification",
                "subject",
                "grade",
                "stream",
                "examination_year"
            ]

            available_columns = [
                column for column in preferred_columns
                if column in academic_df.columns
            ]

            if available_columns:
                st.dataframe(
                    academic_df[available_columns],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Academic records were found, but no displayable columns are available.")
        else:
            st.info("No academic records recorded.")


# ============================================================
# 4. GENERATIVE AI INTERPRETATION OF LIME + SHAP
# ============================================================

def generate_xai_interpretation(
    xai_df,
    programme_name,
    institution_name,
    similarity_score
):
    """
    Convert numerical LIME and SHAP contributions into a simple
    student-facing explanation. The LLM explains the supplied values;
    it does not calculate or change the recommendation.
    """
    api_key = st.secrets.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing from .streamlit/secrets.toml."
        )

    if xai_df is None or xai_df.empty:
        raise ValueError("There are no LIME and SHAP results to explain.")

    required_columns = [
        "Profile Feature",
        "LIME Contribution",
        "SHAP Contribution"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in xai_df.columns
    ]

    if missing_columns:
        raise ValueError(
            "The XAI result is missing columns: "
            + ", ".join(missing_columns)
        )

    contributions = []

    for _, row in xai_df.iterrows():
        contributions.append({
            "profile_feature": str(row["Profile Feature"]),
            "lime_contribution": round(
                float(row["LIME Contribution"]), 5
            ),
            "shap_contribution": round(
                float(row["SHAP Contribution"]), 5
            )
        })

    client = Groq(api_key=api_key)

    prompt = f"""
Explain these local explainable-AI results to a Sri Lankan school leaver.

Programme: {programme_name}
Institution: {institution_name}
Cosine similarity score: {float(similarity_score):.4f}

LIME and SHAP feature contributions:
{contributions}

Instructions:
- Explain which profile factors contributed positively to similarity.
- Explain which factors contributed negatively, if any.
- Give the greatest attention to the strongest contributions.
- If LIME and SHAP differ, describe that carefully.
- Use simple, supportive language and short paragraphs.
- Explain that a positive contribution increases similarity to this
  programme's content, while a negative contribution decreases it.
- Do not invent student information or programme requirements.
- Do not claim that the student is eligible for admission.
- Do not interpret similarity as admission probability.
- Do not guarantee admission or employment.
- End with a short practical takeaway.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are CareerGuide.AI. Explain numerical local "
                    "XAI results accurately and in plain language. "
                    "Never invent facts or change the meaning of values."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_completion_tokens=400,
        temperature=0.2
    )

    answer = response.choices[0].message.content

    if not answer:
        raise RuntimeError("The AI model returned an empty explanation.")

    return answer


# ============================================================
# 5. DISPLAY INDIVIDUAL RECOMMENDATION
# ============================================================

def display_recommendation(
    row,
    index,
    columns,
    monthly_budget,
    model_input
):

    rank = safe_value(row, columns["rank"], index + 1)

    name = display_value(
        safe_value(row, columns["name"]),
        "Programme name unavailable"
    )

    institution = display_value(
        safe_value(row, columns["institution"]),
        "Institution unavailable"
    )

    institution_type = display_value(
        safe_value(row, columns["type"]),
        "Unknown"
    )

    career_field = display_value(
        safe_value(row, columns["field"]),
        "Not specified"
    )

    qualification = display_value(
        safe_value(row, columns["qualification"])
    )

    location = display_value(
        safe_value(row, columns["location"])
    )

    duration = display_value(
        safe_value(row, columns["duration"])
    )

    study_mode = display_value(
        safe_value(row, columns["study_mode"])
    )

    tuition_fee = display_value(
        safe_value(row, columns["fee"])
    )

    currency = display_value(
        safe_value(row, columns["currency"]),
        ""
    )

    fee_status = safe_value(
        row,
        columns["fee_status"],
        None
    )

    official_url = valid_url(
        safe_value(row, columns["url"], "")
    )

    score = safe_value(
        row,
        columns["score"],
        None
    )

    academic_original = safe_value(
        row,
        columns["academic"],
        "Not Assessed"
    )

    explanation = display_value(
        safe_value(row, columns["explanation"]),
        "No explanation was returned by the recommendation model."
    )

    matched_features = safe_value(
        row,
        columns["matched_features"],
        None
    )

    academic_display = assess_academic_status(academic_original)

    financial_display = assess_financial_status(
        monthly_budget,
        institution_type,
        fee_status
    )

    xai_key = f"xai_result_{index}_{rank}"
    ai_key = f"xai_ai_interpretation_{index}_{rank}"

    # --------------------------------------------------------
    # RECOMMENDATION CARD
    # --------------------------------------------------------

    with st.container(border=True):

        left, right = st.columns([3, 1])

        with left:
            st.markdown(f"### #{rank} {name}")
            st.write(f"**Institution:** {institution}")
            st.caption(
                f"{institution_type} | Career field: {career_field}"
            )

        with right:

            if score is not None:
                try:
                    numeric_score = float(score)

                    # The recommender's matching score is normally
                    # expressed as a percentage (cosine * 100).
                    st.metric(
                        "Profile Match",
                        f"{numeric_score:.2f}%"
                    )
                except (TypeError, ValueError):
                    st.metric("Profile Match", str(score))
            else:
                st.metric("Profile Match", "N/A")

        st.divider()

        st.markdown("**Programme Information**")

        info1, info2, info3 = st.columns(3)

        info1.write("**Qualification**")
        info1.write(qualification)

        info2.write("**Duration**")
        info2.write(duration)

        info3.write("**Study Mode**")
        info3.write(study_mode)

        info4, info5 = st.columns(2)

        info4.write("**Location**")
        info4.write(location)

        info5.write("**Tuition Fee**")

        if tuition_fee != "Not available":
            fee_display = tuition_fee
            if currency:
                fee_display += f" {currency}"
            info5.write(fee_display)
        elif display_value(fee_status, "").lower() == "free":
            info5.write("Listed as Free")
        else:
            info5.write("Not available")

        # Academic and financial assessments
        st.divider()

        status_col1, status_col2 = st.columns(2)

        with status_col1:
            st.markdown("**Academic Assessment**")
            st.info(academic_display)

        with status_col2:
            st.markdown("**Financial Assessment**")

            if financial_display in ["Affordable", "Listed as Free"]:
                st.success(financial_display)
            elif financial_display == "Not Affordable":
                st.warning(financial_display)
            else:
                st.info(financial_display)

        # ----------------------------------------------------
        # XAI + GENERATIVE AI EXPLANATION
        # ----------------------------------------------------

        with st.expander("Why was this programme recommended?"):

            st.write(explanation)

            matched_text = display_value(
                matched_features,
                ""
            )

            if matched_text:
                st.write("**Matched Features**")
                st.write(matched_text)

            st.divider()

            st.markdown("**LIME + SHAP Explanation**")

            programme_id = safe_value(
                row,
                columns.get("programme_id"),
                None
            )

            if st.button(
                "Generate LIME + SHAP Explanation",
                key=f"xai_explain_{index}_{rank}",
                use_container_width=True
            ):

                with st.spinner("Calculating local explanations..."):

                    try:
                        xai_df, base_score, explained_score = (
                            explain_recommendation(
                                model_input=model_input,
                                programme_id=programme_id,
                                programme_name=name,
                                institution_name=institution
                            )
                        )

                        st.session_state[xai_key] = {
                            "data": xai_df.to_dict(orient="records"),
                            "base_score": float(base_score),
                            "explained_score": float(explained_score)
                        }

                        # Clear an older natural-language explanation
                        # when a new numerical explanation is generated.
                        st.session_state.pop(ai_key, None)

                    except Exception as e:
                        st.error(
                            "Could not generate the LIME/SHAP explanation."
                        )
                        st.exception(e)

            saved_xai = st.session_state.get(xai_key)

            if saved_xai:

                st.write(
                    "**Programme Similarity Score:** "
                    f"{saved_xai['explained_score']:.4f}"
                )

                xai_df = pd.DataFrame(saved_xai["data"])

                st.dataframe(
                    xai_df,
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    "Positive contributions increase similarity; negative "
                    "contributions decrease it. These values explain the "
                    "selected programme's similarity score, not admission "
                    "probability or formal eligibility."
                )

                st.divider()

                st.markdown("**Understand Your Results**")

                if st.button(
                    "✨ Explain My Results in Simple Language",
                    key=f"xai_ai_button_{index}_{rank}",
                    use_container_width=True
                ):

                    with st.spinner(
                        "CareerGuide.AI is explaining your results..."
                    ):

                        try:
                            interpretation = generate_xai_interpretation(
                                xai_df=xai_df,
                                programme_name=name,
                                institution_name=institution,
                                similarity_score=saved_xai["explained_score"]
                            )

                            st.session_state[ai_key] = interpretation

                        except Exception as e:
                            st.error(
                                "Could not generate the simple explanation."
                            )
                            st.exception(e)

                ai_interpretation = st.session_state.get(ai_key)

                if ai_interpretation:
                    st.markdown("### What this means for you")
                    st.markdown(ai_interpretation)

        # Official programme website
        if official_url:
            st.link_button(
                "Visit Official Programme Website",
                official_url,
                use_container_width=True
            )


# ============================================================
# 6. MAIN RECOMMENDATION PAGE
# ============================================================

def show_recommendations(client, user_id):

    st.title("🎯 Personalised Education Recommendations")

    st.write(
        "Explore education programmes matched with your "
        "academic background and interests."
    )

    # --------------------------------------------------------
    # LOAD STUDENT INFORMATION
    # --------------------------------------------------------

    try:
        student = load_student_data(
            client=client,
            user_id=user_id
        )

        if student is None:
            st.warning(
                "Please complete and save your Student Profile first."
            )
            return

    except Exception as e:
        st.error("Could not retrieve your student profile.")
        st.exception(e)
        return

    profile = student["profile"]
    model_input = student["model_input"]

    # --------------------------------------------------------
    # READ MONTHLY BUDGET
    # --------------------------------------------------------

    try:
        monthly_budget = float(profile.get("budget_category"))
    except (TypeError, ValueError):
        monthly_budget = None

    # --------------------------------------------------------
    # PROFILE SUMMARY
    # --------------------------------------------------------

    display_student_summary(
        student,
        monthly_budget
    )

    # --------------------------------------------------------
    # CHECK REQUIRED MODEL INPUTS
    # --------------------------------------------------------

    required_fields = [
        "Student_Stage",
        "Interests_Select_Up_to_3",
        "Education_Preference"
    ]

    missing = [
        field
        for field in required_fields
        if not str(model_input.get(field, "") or "").strip()
    ]

    if missing:
        st.warning(
            "Please complete these profile fields before generating "
            "recommendations: " + ", ".join(missing)
        )
        return

    st.divider()

    st.subheader("Generate Your Recommendations")

    st.write(
        "The recommendation engine analyses your profile "
        "and identifies the ten most similar education programmes."
    )

    # --------------------------------------------------------
    # GENERATE RECOMMENDATIONS
    # --------------------------------------------------------

    if st.button(
        "✨ Generate My Top 10 Recommendations",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "Analysing your profile and finding matching programmes..."
        ):

            try:
                results = recommend_programmes(
                    model_input,
                    top_k=10
                )

                if results is None or results.empty:
                    st.warning("No recommendations were generated.")
                    return

                st.session_state["career_recommendations"] = (
                    results.to_dict(orient="records")
                )

                st.session_state["career_recommendation_user"] = user_id

                # Clear old XAI explanations for previous recommendations.
                for key in list(st.session_state.keys()):
                    if (
                        str(key).startswith("xai_result_")
                        or str(key).startswith("xai_ai_interpretation_")
                    ):
                        del st.session_state[key]

            except Exception as e:
                st.error("Recommendation generation failed.")
                st.exception(e)
                return

    # --------------------------------------------------------
    # RETRIEVE GENERATED RESULTS
    # --------------------------------------------------------

    saved_results = st.session_state.get("career_recommendations")
    saved_user = st.session_state.get("career_recommendation_user")

    if not saved_results or saved_user != user_id:
        return

    results = pd.DataFrame(saved_results)

    # --------------------------------------------------------
    # RESULT SUMMARY
    # --------------------------------------------------------

    st.divider()

    st.subheader("Your Top 10 Recommended Programmes")

    st.caption(
        "Recommendations are ranked using TF-IDF content similarity. "
        "The matching score represents profile similarity, "
        "not admission probability or guaranteed eligibility."
    )

    total_results = len(results)

    score_col = find_column(
        results,
        [
            "matching_score",
            "matching_score_percent",
            "similarity_score",
            "score"
        ]
    )

    average_score = None

    if score_col:
        numeric_scores = pd.to_numeric(
            results[score_col],
            errors="coerce"
        ).dropna()

        if not numeric_scores.empty:
            average_score = numeric_scores.mean()

    col1, col2 = st.columns(2)

    col1.metric(
        "Programmes Recommended",
        total_results
    )

    col2.metric(
        "Average Profile Match",
        f"{average_score:.2f}%"
        if average_score is not None
        else "N/A"
    )

    # --------------------------------------------------------
    # IDENTIFY RESULT COLUMNS
    # --------------------------------------------------------

    columns = {
        "programme_id": find_column(
            results, ["programme_id", "program_id"]
        ),
        "name": find_column(
            results, ["programme_name"]
        ),
        "institution": find_column(
            results, ["institution_name"]
        ),
        "type": find_column(
            results, ["institution_type", "sector"]
        ),
        "field": find_column(
            results, ["career_field"]
        ),
        "qualification": find_column(
            results, ["qualification_type"]
        ),
        "location": find_column(
            results, ["location", "district"]
        ),
        "duration": find_column(
            results, ["duration"]
        ),
        "study_mode": find_column(
            results, ["study_mode"]
        ),
        "fee": find_column(
            results, ["total_tuition_fee"]
        ),
        "currency": find_column(
            results, ["fee_currency"]
        ),
        "fee_status": find_column(
            results, ["fee_status"]
        ),
        "url": find_column(
            results, ["official_url"]
        ),
        "score": score_col,
        "rank": find_column(
            results, ["recommendation_rank", "rank"]
        ),
        "academic": find_column(
            results, ["academic_eligibility", "eligibility_status"]
        ),
        "explanation": find_column(
            results, ["xai_explanation", "explanation"]
        ),
        "matched_features": find_column(
            results, ["matched_features", "matched_terms"]
        )
    }

    # --------------------------------------------------------
    # DISPLAY RECOMMENDATIONS
    # --------------------------------------------------------

    for index, row in results.iterrows():
        display_recommendation(
            row,
            index,
            columns,
            monthly_budget,
            model_input
        )

    # --------------------------------------------------------
    # DOWNLOAD RESULTS
    # --------------------------------------------------------

    st.divider()

    st.subheader("Download Your Results")

    csv_data = results.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "⬇️ Download Recommendations (CSV)",
        data=csv_data,
        file_name="CareerGuide_AI_Recommendations.csv",
        mime="text/csv",
        use_container_width=True
    )

