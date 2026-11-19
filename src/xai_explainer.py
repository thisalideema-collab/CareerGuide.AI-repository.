
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
import streamlit as st

from lime.lime_tabular import LimeTabularExplainer
from sklearn.metrics.pairwise import cosine_similarity


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "career_guide_recommender.joblib"
)

FEATURES = [
    "Student Stage",
    "A/L Stream",
    "Interests",
    "Education Preference",
]

INPUT_KEYS = [
    "Student_Stage",
    "AL_Stream",
    "Interests_Select_Up_to_3",
    "Education_Preference",
]


@st.cache_resource
def load_xai_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}"
        )

    package = joblib.load(MODEL_PATH)

    required = [
        "vectorizer",
        "programme_vectors",
        "programme_metadata",
    ]

    missing = [
        key for key in required
        if key not in package
    ]

    if missing:
        raise KeyError(
            "Missing model package keys: "
            + ", ".join(missing)
        )

    return package


def normalise(value):

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).strip()
    ).casefold()


def find_column(df, candidates):

    lookup = {
        str(column).strip().casefold(): column
        for column in df.columns
    }

    for candidate in candidates:

        if candidate.casefold() in lookup:
            return lookup[candidate.casefold()]

    return None


def find_programme_index(
    package,
    programme_id,
    programme_name,
    institution_name
):

    metadata = package["programme_metadata"]

    if not isinstance(metadata, pd.DataFrame):
        metadata = pd.DataFrame(metadata)

    id_col = find_column(
        metadata,
        ["programme_id"]
    )

    name_col = find_column(
        metadata,
        ["programme_name"]
    )

    institution_col = find_column(
        metadata,
        ["institution_name"]
    )

    # First try Programme_ID.
    if programme_id is not None and id_col:

        matches = metadata.index[
            metadata[id_col].astype(str)
            == str(programme_id)
        ].tolist()

        if matches:
            return int(matches[0])

    # Otherwise match programme and institution names.
    if name_col and institution_col:

        matches = metadata.index[
            metadata[name_col].map(normalise).eq(
                normalise(programme_name)
            )
            &
            metadata[institution_col].map(normalise).eq(
                normalise(institution_name)
            )
        ].tolist()

        if matches:
            return int(matches[0])

    raise ValueError(
        "Programme could not be matched with the saved model metadata."
    )


def explain_recommendation(
    model_input,
    programme_id=None,
    programme_name=None,
    institution_name=None
):

    package = load_xai_model()

    vectorizer = package["vectorizer"]

    programme_vectors = package["programme_vectors"]

    target_index = find_programme_index(
        package,
        programme_id,
        programme_name,
        institution_name
    )

    target_vector = programme_vectors[target_index]

    # Build profile text using the four trained model inputs.
    def build_text(mask):

        values = []

        for include, key in zip(mask, INPUT_KEYS):

            if include >= 0.5:

                value = model_input.get(key, "")

                if value is not None:

                    value = str(value).strip()

                    if value and value.casefold() not in [
                        "nan", "none", "null"
                    ]:
                        values.append(value)

        return " ".join(values)

    # Calculate cosine similarity for each perturbed profile.
    def predict_similarity(mask_matrix):

        mask_matrix = np.asarray(
            mask_matrix,
            dtype=float
        )

        if mask_matrix.ndim == 1:
            mask_matrix = mask_matrix.reshape(1, -1)

        texts = [
            build_text(mask)
            for mask in mask_matrix
        ]

        vectors = vectorizer.transform(texts)

        scores = cosine_similarity(
            vectors,
            target_vector
        ).ravel()

        return scores

    full_mask = np.ones(4, dtype=float)

    empty_mask = np.zeros(4, dtype=float)

    explained_score = float(
        predict_similarity(full_mask)[0]
    )

    base_score = float(
        predict_similarity(empty_mask)[0]
    )

    # -------------------------------
    # LIME EXPLANATION
    # -------------------------------

    lime = LimeTabularExplainer(
        training_data=np.array([
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
        ], dtype=float),

        feature_names=FEATURES,

        mode="regression",

        discretize_continuous=False,

        random_state=42
    )

    lime_exp = lime.explain_instance(
        full_mask,
        predict_similarity,
        num_features=4,
        num_samples=1000
    )

    lime_values = {
        feature: 0.0
        for feature in FEATURES
    }

    for label, contribution in lime_exp.as_list():

        matched = next(
            (
                feature
                for feature in FEATURES
                if label.strip().startswith(feature)
            ),
            None
        )

        if matched:
            lime_values[matched] = float(contribution)

    # -------------------------------
    # SHAP EXPLANATION
    # -------------------------------

    shap_explainer = shap.KernelExplainer(
        predict_similarity,
        np.zeros((1, 4), dtype=float)
    )

    shap_raw = shap_explainer.shap_values(
        full_mask.reshape(1, -1),
        nsamples=100
    )

    if isinstance(shap_raw, list):
        shap_raw = shap_raw[0]

    shap_values = np.asarray(
        shap_raw,
        dtype=float
    ).reshape(-1)

    if len(shap_values) != 4:

        raise ValueError(
            "SHAP returned an unexpected number of features."
        )

    # -------------------------------
    # FINAL EXPLANATION TABLE
    # -------------------------------

    result = pd.DataFrame({

        "Profile Feature": FEATURES,

        "LIME Contribution": [
            lime_values[feature]
            for feature in FEATURES
        ],

        "SHAP Contribution": shap_values

    })

    return result, base_score, explained_score

# ============================================================
# 6. GENERATIVE AI EXPLANATION OF LIME + SHAP RESULTS
# ============================================================

def generate_xai_interpretation(
    xai_df,
    programme_name,
    institution_name,
    similarity_score
):

    from groq import Groq

    try:

        api_key = st.secrets["GROQ_API_KEY"]

        client = Groq(api_key=api_key)

        explanation_data = []

        for _, row in xai_df.iterrows():

            explanation_data.append({
                "feature": row["Profile Feature"],
                "lime_contribution": round(
                    float(row["LIME Contribution"]), 4
                ),
                "shap_contribution": round(
                    float(row["SHAP Contribution"]), 4
                )
            })

        prompt = f"""
Explain the following AI recommendation results to a Sri Lankan
school leaver in simple, friendly and understandable language.

PROGRAMME:
{programme_name}

INSTITUTION:
{institution_name}

COSINE SIMILARITY SCORE:
{similarity_score:.4f}

LIME AND SHAP RESULTS:
{explanation_data}

INSTRUCTIONS:

1. Explain which student profile factors contributed most positively.
2. Explain any negative contributions without alarming the student.
3. Compare the LIME and SHAP results where useful.
4. Explain what the results mean for this particular programme.
5. Use simple language suitable for a school leaver.
6. Give a short, helpful conclusion.
7. Do not invent student information.
8. Do not claim that the student is academically eligible.
9. Do not interpret similarity as admission probability.
10. Do not guarantee admission or employment.

Use short paragraphs and clear language.
Address the student directly.
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are CareerGuide.AI, an educational "
                        "guidance assistant. Explain AI model "
                        "results accurately and simply."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_completion_tokens=350
        )

        answer = response.choices[0].message.content

        if not answer:
            return "An explanation could not be generated. Please try again."

        return answer

    except Exception as e:

        raise RuntimeError(
            f"Could not generate the AI explanation: {str(e)}"
        )
