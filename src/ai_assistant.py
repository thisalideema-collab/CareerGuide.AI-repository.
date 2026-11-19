
import re
import json
import streamlit as st

from groq import Groq
from src.database import get_all_programmes


# ============================================================
# 1. GROQ CONFIGURATION
# ============================================================

MODEL_NAME = "openai/gpt-oss-120b"


def get_groq_client():

    try:
        api_key = st.secrets["GROQ_API_KEY"]

        if not api_key:
            st.error("Groq API key is missing.")
            return None

        return Groq(api_key=api_key)

    except Exception as e:
        st.error(f"Groq configuration error: {e}")
        return None


# ============================================================
# 2. FIND RELEVANT PROGRAMMES
# ============================================================

def get_relevant_programmes(question, programmes, limit=2):

    if not programmes:
        return []

    question_words = set(
        re.findall(r"[a-zA-Z]{3,}", question.lower())
    )

    stop_words = {
        "what", "where", "when", "which", "who",
        "how", "can", "could", "would", "should",
        "the", "and", "for", "are", "you", "your",
        "with", "from", "about", "after", "before",
        "this", "that", "have", "has", "does"
    }

    question_words -= stop_words

    searchable_fields = [
        "programme_name",
        "institution_name",
        "institution_type",
        "career_field",
        "qualification_type",
        "faculty",
        "district",
        "location"
    ]

    scored_programmes = []

    for programme in programmes:

        searchable_text = " ".join(
            str(programme.get(field, "") or "")
            for field in searchable_fields
        ).lower()

        score = sum(
            1 for word in question_words
            if word in searchable_text
        )

        if score > 0:

            scored_programmes.append(
                (score, programme)
            )

    scored_programmes.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        programme
        for score, programme in scored_programmes[:limit]
    ]


# ============================================================
# 3. PREPARE SMALL PROGRAMME CONTEXT
# ============================================================

def prepare_programme_context(programmes):

    if not programmes:

        return (
            "No directly matching programme records were found "
            "in the database."
        )

    selected_fields = [
        "programme_name",
        "institution_name",
        "institution_type",
        "career_field",
        "qualification_type",
        "district",
        "duration",
        "study_mode",
        "total_tuition_fee",
        "fee_currency",
        "fee_status",
        "entry_requirements",
        "official_url"
    ]

    context = []

    for programme in programmes:

        record = {}

        for field in selected_fields:

            value = programme.get(field)

            if value is None:
                value = "Not available"

            # Limit long database fields.
            value = str(value).strip()[:250]

            record[field] = value

        context.append(record)

    return json.dumps(
        context,
        ensure_ascii=False,
        indent=1
    )


# ============================================================
# 4. GENERATE AI RESPONSE
# ============================================================

def generate_ai_response(
    question,
    chat_history,
    programmes
):

    client = get_groq_client()

    if client is None:
        return None

    # Retrieve only two relevant programme records.
    relevant_programmes = get_relevant_programmes(
        question,
        programmes,
        limit=2
    )

    programme_context = prepare_programme_context(
        relevant_programmes
    )

    system_prompt = """
You are CareerGuide.AI, a helpful Sri Lankan education
and career guidance assistant.

Help students understand:
- Higher education opportunities
- Career pathways
- University and vocational programmes
- Qualifications
- Education planning

IMPORTANT RULES:

1. Give clear and practical answers.
2. Use supplied database records for programme-specific facts.
3. Never invent institutions, programmes, fees or requirements.
4. If information is missing, say it is not available.
5. Never guarantee admission or employment.
6. Do not claim formal admission eligibility.
7. Recommend checking official institution websites.
8. Distinguish general career advice from verified facts.
9. Respond in the student's language where possible.

You are an educational guidance assistant, not an
official admission authority.
"""

    user_message = f"""
STUDENT QUESTION:
{question[:700]}

RELEVANT DATABASE INFORMATION:
{programme_context}

Answer the student's question clearly.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # Keep only the last four short chat messages.
    recent_history = chat_history[-4:]

    for message in recent_history:

        content = str(
            message.get("content", "")
        )[:600]

        role = message.get("role")

        if role in ["user", "assistant"] and content:

            messages.append({
                "role": role,
                "content": content
            })

    messages.append({
        "role": "user",
        "content": user_message
    })

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_completion_tokens=700
        )

        answer = response.choices[0].message.content

        if not answer:
            return "I could not generate a response. Please try again."

        return answer

    except Exception as e:

        error_message = str(e)

        if "rate_limit_exceeded" in error_message:

            st.error(
                "The Groq token limit has been reached. "
                "Please wait a short time and try again."
            )

        else:

            st.error("AI response generation failed.")
            st.exception(e)

        return None


# ============================================================
# 5. MAIN AI CAREER ASSISTANT INTERFACE
# ============================================================

def show_ai_assistant():

    st.title("🤖 AI Career Assistant")

    st.write(
        "Ask questions about education opportunities, "
        "career pathways and higher education programmes "
        "in Sri Lanka."
    )

    st.info(
        "CareerGuide.AI provides conversational guidance "
        "using an AI language model and available programme data."
    )

    # --------------------------------------------------------
    # LOAD PROGRAMMES
    # --------------------------------------------------------

    try:

        programmes = get_all_programmes()

        if not programmes:
            st.warning(
                "Programme information is currently unavailable."
            )

    except Exception as e:

        programmes = []

        st.error("Could not load programme information.")
        st.exception(e)

    # --------------------------------------------------------
    # INITIALISE CHAT
    # --------------------------------------------------------

    if "career_ai_messages" not in st.session_state:

        st.session_state["career_ai_messages"] = []

    # --------------------------------------------------------
    # EXAMPLE QUESTIONS
    # --------------------------------------------------------

    st.subheader("Example Questions")

    examples = [
        "What career pathways are available after A/L?",
        "What is the difference between a degree and a diploma?",
        "What IT programmes are available in Sri Lanka?",
        "How can I choose a suitable career?",
        "What should I consider before selecting a university?"
    ]

    selected_question = None

    for i in range(0, len(examples), 2):

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                examples[i],
                key=f"example_question_{i}",
                use_container_width=True
            ):

                selected_question = examples[i]

        if i + 1 < len(examples):

            with col2:

                if st.button(
                    examples[i + 1],
                    key=f"example_question_{i+1}",
                    use_container_width=True
                ):

                    selected_question = examples[i + 1]

    st.divider()

    # --------------------------------------------------------
    # DISPLAY CHAT HISTORY
    # --------------------------------------------------------

    st.subheader("Chat with CareerGuide.AI")

    for message in st.session_state["career_ai_messages"]:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    # --------------------------------------------------------
    # USER INPUT
    # --------------------------------------------------------

    user_question = st.chat_input(
        "Ask your education or career question..."
    )

    if selected_question:

        user_question = selected_question

    # --------------------------------------------------------
    # GENERATE RESPONSE
    # --------------------------------------------------------

    if user_question:

        previous_history = (
            st.session_state["career_ai_messages"].copy()
        )

        st.session_state["career_ai_messages"].append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):

            st.markdown(user_question)

        with st.chat_message("assistant"):

            with st.spinner(
                "CareerGuide.AI is preparing your answer..."
            ):

                answer = generate_ai_response(
                    question=user_question,
                    chat_history=previous_history,
                    programmes=programmes
                )

            if answer:

                st.markdown(answer)

                st.session_state["career_ai_messages"].append({
                    "role": "assistant",
                    "content": answer
                })

    # --------------------------------------------------------
    # CLEAR CONVERSATION
    # --------------------------------------------------------

    st.divider()

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True
    ):

        st.session_state["career_ai_messages"] = []

        st.rerun()

