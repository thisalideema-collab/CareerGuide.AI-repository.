
import os
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# 1. MODEL LOCATION AND LOADING
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_PATH = os.path.join(
    PROJECT_ROOT,
    "models",
    "career_guide_recommender.joblib"
)


@lru_cache(maxsize=1)
def load_recommender():
    """
    Load the saved TF-IDF recommendation model once per app process.

    The model file must be:
    models/career_guide_recommender.joblib
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Saved recommendation model was not found: {MODEL_PATH}"
        )

    model = joblib.load(MODEL_PATH)

    required_keys = [
        "vectorizer",
        "programme_vectors",
        "programme_metadata"
    ]

    missing_keys = [
        key for key in required_keys
        if key not in model
    ]

    if missing_keys:
        raise KeyError(
            "The saved model is missing required items: "
            + ", ".join(missing_keys)
        )

    if len(model["programme_metadata"]) != model["programme_vectors"].shape[0]:
        raise ValueError(
            "The programme metadata row count does not match "
            "the number of saved programme vectors."
        )

    return model


# ============================================================
# 2. DATA HELPERS
# ============================================================

def get_value(record, *possible_names, default=None):
    """Read a value using either PascalCase or snake_case column names."""
    if record is None:
        return default

    if isinstance(record, pd.Series):
        items = record.to_dict()
    elif isinstance(record, dict):
        items = record
    else:
        return default

    normalised = {
        str(key).strip().lower().replace(" ", "_"): value
        for key, value in items.items()
    }

    for name in possible_names:
        key = str(name).strip().lower().replace(" ", "_")

        if key in normalised:
            value = normalised[key]

            if value is None:
                return default

            try:
                if pd.isna(value):
                    return default
            except (TypeError, ValueError):
                pass

            return value

    return default


def is_true(value):
    """Safely interpret boolean values stored as bools or strings."""
    if isinstance(value, (bool, np.bool_)):
        return bool(value)

    if value is None:
        return False

    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass

    return str(value).strip().lower() in {
        "true", "1", "yes", "y"
    }


def clean_text(value):
    """Convert missing values to an empty string."""
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    if text.lower() in {"nan", "none", "null"}:
        return ""

    return text


# ============================================================
# 3. BUILD STUDENT PROFILE
# ============================================================

def build_student_profile(student_data):
    """
    Build the text profile using the same four fields used
    during the original TF-IDF model development.

    The current model uses:
    Student_Stage, AL_Stream, Interests_Select_Up_to_3,
    Education_Preference.
    """
    profile_columns = [
        "Student_Stage",
        "AL_Stream",
        "Interests_Select_Up_to_3",
        "Education_Preference"
    ]

    profile_parts = []

    for column in profile_columns:
        value = clean_text(student_data.get(column, ""))

        if value:
            profile_parts.append(value)

    return " ".join(profile_parts)


# ============================================================
# 4. ACADEMIC REQUIREMENT CHECK
# ============================================================

def check_academic_status(student, programme):
    """
    This is a cautious screening indicator, not a formal
    admission-eligibility decision.
    """
    required_stream = clean_text(
        get_value(
            programme,
            "Required_AL_Stream",
            "required_al_stream"
        )
    )

    student_stream = clean_text(
        student.get("AL_Stream", "")
    )

    requirements_available = is_true(
        get_value(
            programme,
            "Requirements_Available",
            "requirements_available",
            default=False
        )
    )

    if not requirements_available:
        return "Not Assessed"

    if required_stream and student_stream:
        if required_stream.casefold() != student_stream.casefold():
            return "Potential Stream Mismatch"

    # A matching or missing stream does not prove eligibility.
    return "Needs Verification"


# ============================================================
# 5. FINANCIAL INFORMATION CLASSIFICATION
# ============================================================

def check_financial_status(programme):
    """
    Classify the availability of programme fee information.
    Missing fees are never treated as free.
    """
    fee = get_value(
        programme,
        "Total_Tuition_Fee",
        "total_tuition_fee",
        default=None
    )

    currency = clean_text(
        get_value(
            programme,
            "Fee_Currency",
            "fee_currency"
        )
    )

    fee_status = clean_text(
        get_value(
            programme,
            "Fee_Status",
            "fee_status"
        )
    )

    if "free" in fee_status.casefold():
        return "Listed as Free"

    if fee is None or clean_text(fee) == "":
        return "Unknown - Missing Financial Data"

    if not currency:
        return "Unknown - Currency Missing"

    return "Needs Currency Verification"


# ============================================================
# 6. TF-IDF EXPLANATION
# ============================================================

def generate_explanation(
    student_vector,
    programme_vector,
    feature_names,
    max_features=5
):
    """
    Identify the strongest shared TF-IDF terms contributing
    to the cosine similarity score.
    """
    contributions = student_vector.multiply(
        programme_vector
    ).tocoo()

    if contributions.nnz == 0:
        return (
            "No shared TF-IDF terms contributed "
            "to this recommendation.",
            []
        )

    sorted_positions = np.argsort(
        -contributions.data
    )[:max_features]

    matched_features = [
        str(feature_names[contributions.col[position]])
        for position in sorted_positions
    ]

    explanation = (
        "This programme matched the student's profile through "
        "the following contributing terms: "
        + ", ".join(matched_features)
        + "."
    )

    return explanation, matched_features


# ============================================================
# 7. MAIN RECOMMENDATION FUNCTION
# ============================================================

def recommend_programmes(student_data, top_k=10):
    """
    Generate the top-k programme recommendations for one student.

    Returns a pandas DataFrame with the programme information,
    similarity score, academic/financial screening indicators,
    and TF-IDF explanation.
    """
    if not isinstance(student_data, dict):
        raise TypeError("student_data must be a dictionary.")

    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    model = load_recommender()

    vectorizer = model["vectorizer"]
    programme_vectors = model["programme_vectors"]
    metadata = model["programme_metadata"].copy()

    student_profile = build_student_profile(student_data)

    if not student_profile.strip():
        raise ValueError(
            "Please provide at least one student profile detail."
        )

    if metadata.empty or programme_vectors.shape[0] == 0:
        return pd.DataFrame()

    # Transform the student profile using the saved vectorizer.
    student_vector = vectorizer.transform([student_profile])

    # Calculate cosine similarity against all programme vectors.
    scores = cosine_similarity(
        student_vector,
        programme_vectors
    )[0]

    if len(scores) != len(metadata):
        raise ValueError(
            "Similarity score count does not match programme metadata."
        )

    # Select the highest-scoring programmes.
    top_indices = np.argsort(-scores)[
        :min(top_k, len(scores))
    ]

    feature_names = vectorizer.get_feature_names_out()

    results = []

    for rank, index in enumerate(top_indices, start=1):

        programme = metadata.iloc[index]
        score = float(scores[index])
        programme_vector = programme_vectors[index]

        explanation, matched_features = generate_explanation(
            student_vector,
            programme_vector,
            feature_names
        )

        academic_status = check_academic_status(
            student_data,
            programme
        )

        financial_status = check_financial_status(
            programme
        )

        # Keep the source programme ID unchanged.
        programme_id = get_value(
            programme,
            "Programme_ID",
            "programme_id"
        )

        results.append({
            "Programme_ID": programme_id,
            "Programme_Name": get_value(
                programme, "Programme_Name", "programme_name"
            ),
            "Institution_Name": get_value(
                programme, "Institution_Name", "institution_name"
            ),
            "Institution_Type": get_value(
                programme, "Institution_Type", "institution_type"
            ),
            "Career_Field": get_value(
                programme, "Career_Field", "career_field"
            ),
            "Qualification_Type": get_value(
                programme, "Qualification_Type", "qualification_type"
            ),
            "Location": get_value(
                programme, "Location", "location"
            ),
            "District": get_value(
                programme, "District", "district"
            ),
            "Duration": get_value(
                programme, "Duration", "duration"
            ),
            "Study_Mode": get_value(
                programme, "Study_Mode", "study_mode"
            ),
            "Total_Tuition_Fee": get_value(
                programme, "Total_Tuition_Fee", "total_tuition_fee"
            ),
            "Fee_Currency": get_value(
                programme, "Fee_Currency", "fee_currency"
            ),
            "Fee_Status": get_value(
                programme, "Fee_Status", "fee_status"
            ),
            "Official_URL": get_value(
                programme, "Official_URL", "official_url"
            ),
            "Required_AL_Stream": get_value(
                programme, "Required_AL_Stream", "required_al_stream"
            ),
            "Required_AL_Subjects": get_value(
                programme, "Required_AL_Subjects", "required_al_subjects"
            ),
            "Requirements_Available": get_value(
                programme, "Requirements_Available",
                "requirements_available", default=False
            ),
            "Matching_Score": round(score * 100, 4),
            "Recommendation_Rank": rank,
            "Eligibility_Status": "Needs Verification",
            "Academic_Eligibility": academic_status,
            "Financial_Feasibility": financial_status,
            "XAI_Explanation": explanation,
            "Matched_Features": "; ".join(matched_features)
        })

    return pd.DataFrame(results)
