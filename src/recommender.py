
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics.pairwise import cosine_similarity


# --------------------------------------------------
# 1. LOAD THE SAVED MODEL
# --------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_PATH = os.path.join(
    PROJECT_ROOT,
    "models",
    "career_guide_recommender.joblib"
)


def load_recommender():
    """Load the previously trained TF-IDF model."""

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}"
        )

    model = joblib.load(MODEL_PATH)

    return model


# --------------------------------------------------
# 2. BUILD STUDENT PROFILE
# --------------------------------------------------

def build_student_profile(student_data):
    """
    Build text profile using the same four fields
    used during the original model development.
    """

    profile_columns = [
        "Student_Stage",
        "AL_Stream",
        "Interests_Select_Up_to_3",
        "Education_Preference"
    ]

    profile_parts = []

    for column in profile_columns:
        value = student_data.get(column, "")

        if value is not None and not pd.isna(value):
            value = str(value).strip()

            if value:
                profile_parts.append(value)

    return " ".join(profile_parts)


# --------------------------------------------------
# 3. ACADEMIC VERIFICATION
# --------------------------------------------------

def check_academic_status(student, programme):

    required_stream = str(
        programme.get("Required_AL_Stream", "") or ""
    ).strip()

    student_stream = str(
        student.get("AL_Stream", "") or ""
    ).strip()

    requirements_available = programme.get(
        "Requirements_Available", False
    )

    if pd.isna(requirements_available):
        requirements_available = False

    if not bool(requirements_available):
        return "Not Assessed"

    if required_stream and student_stream:
        if required_stream.lower() != student_stream.lower():
            return "Potential Stream Mismatch"

    return "Needs Verification"


# --------------------------------------------------
# 4. FINANCIAL CLASSIFICATION
# --------------------------------------------------

def check_financial_status(programme):

    fee = programme.get("Total_Tuition_Fee", np.nan)

    currency = str(
        programme.get("Fee_Currency", "") or ""
    ).strip()

    fee_status = str(
        programme.get("Fee_Status", "") or ""
    ).strip()

    if "free" in fee_status.lower():
        return "Listed as Free"

    if pd.isna(fee):
        return "Unknown - Missing Financial Data"

    if not currency:
        return "Unknown - Currency Missing"

    return "Needs Currency Verification"


# --------------------------------------------------
# 5. GENERATE XAI EXPLANATION
# --------------------------------------------------

def generate_explanation(
    student_vector,
    programme_vector,
    feature_names
):
    """
    Identify shared TF-IDF terms and their
    mathematical contribution to similarity.
    """

    contributions = student_vector.multiply(
        programme_vector
    ).tocoo()

    if contributions.nnz == 0:
        return (
            "No shared TF-IDF terms contributed "
            "to this recommendation."
        ), []

    sorted_positions = np.argsort(
        -contributions.data
    )[:5]

    matched_features = [
        str(feature_names[contributions.col[position]])
        for position in sorted_positions
    ]

    explanation = (
        "This programme matched the student's profile "
        "through the following contributing terms: "
        + ", ".join(matched_features)
        + "."
    )

    return explanation, matched_features


# --------------------------------------------------
# 6. MAIN RECOMMENDATION FUNCTION
# --------------------------------------------------

def recommend_programmes(student_data, top_k=10):

    model = load_recommender()

    vectorizer = model["vectorizer"]

    programme_vectors = model["programme_vectors"]

    metadata = model["programme_metadata"].copy()

    # Build student profile
    student_profile = build_student_profile(
        student_data
    )

    if not student_profile.strip():
        raise ValueError(
            "Please provide at least one student profile detail."
        )

    # Transform student profile using saved vectorizer
    student_vector = vectorizer.transform(
        [student_profile]
    )

    # Calculate cosine similarity
    scores = cosine_similarity(
        student_vector,
        programme_vectors
    )[0]

    # Select top programmes
    top_indices = np.argsort(-scores)[
        :min(top_k, len(scores))
    ]

    feature_names = vectorizer.get_feature_names_out()

    results = []

    for rank, index in enumerate(top_indices, start=1):

        programme = metadata.iloc[index]

        score = float(scores[index])

        programme_vector = programme_vectors[index]

        # Generate XAI explanation
        explanation, matched_features = (
            generate_explanation(
                student_vector,
                programme_vector,
                feature_names
            )
        )

        # Academic verification
        academic_status = check_academic_status(
            student_data,
            programme
        )

        # Financial classification
        financial_status = check_financial_status(
            programme
        )

        results.append({
            "Programme_ID": programme.get("Programme_ID"),
            "Programme_Name": programme.get("Programme_Name"),
            "Institution_Name": programme.get("Institution_Name"),
            "Institution_Type": programme.get("Institution_Type"),
            "Career_Field": programme.get("Career_Field"),
            "Qualification_Type": programme.get("Qualification_Type"),
            "Location": programme.get("Location"),
            "District": programme.get("District"),
            "Duration": programme.get("Duration"),
            "Study_Mode": programme.get("Study_Mode"),
            "Total_Tuition_Fee": programme.get("Total_Tuition_Fee"),
            "Fee_Currency": programme.get("Fee_Currency"),
            "Fee_Status": programme.get("Fee_Status"),
            "Official_URL": programme.get("Official_URL"),
            "Matching_Score": round(score * 100, 4),
            "Recommendation_Rank": rank,
            "Eligibility_Status": "Needs Verification",
            "Academic_Eligibility": academic_status,
            "Financial_Feasibility": financial_status,
            "XAI_Explanation": explanation,
            "Matched_Features": "; ".join(matched_features)
        })

    return pd.DataFrame(results)
