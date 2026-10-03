import streamlit as st
from dotenv import load_dotenv

from services.search import (
    discover_university,
    search_university_sources,
)
from services.llm import answer_with_gemma
from services.tts import text_to_speech
from services.verify import rank_and_verify_sources
from services.storage import load_universities, save_universities


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CampusQuery AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# SIMPLE UI STYLE
# No HTML cards are used for answers/sources.
# =========================================================

st.markdown("""
<style>

/* ================================
   GLOBAL
   ================================ */

.stApp {
    background: #f7f9fc;
    color: #000000 !important;
}

body {
    color: #000000 !important;
}


/* ================================
   DARK HERO / HEADER
   ================================ */

.hero {
    padding: 28px 32px;
    border-radius: 22px;
    background: linear-gradient(135deg, #111827, #1e3a8a);
    color: #ffffff !important;
    margin-bottom: 20px;
}

.hero h1 {
    margin: 0;
    font-size: 42px;
    color: #ffffff !important;
}

.hero p {
    margin: 8px 0 0;
    color: #ffffff !important;
    font-size: 17px;
}


/* ================================
   WHITE CARDS
   ================================ */

.card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 14px;
    color: #000000 !important;
}

.card h1,
.card h2,
.card h3,
.card p,
.card span,
.card div {
    color: #000000 !important;
}


/* ================================
   SIDEBAR - WHITE BACKGROUND
   ================================ */

section[data-testid="stSidebar"] {
    background: #ffffff !important;
    color: #000000 !important;
}

section[data-testid="stSidebar"] * {
    color: #000000 !important;
}


/* ================================
   INPUT BOXES - WHITE BACKGROUND
   ================================ */

.stTextInput input,
.stTextArea textarea,
.stSelectbox input {
    background: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #d1d5db !important;
}


/* Selectbox text */
div[data-baseweb="select"] {
    background: #ffffff !important;
    color: #000000 !important;
}

div[data-baseweb="select"] * {
    color: #000000 !important;
}


/* ================================
   CHAT AREA
   ================================ */

.stChatMessage {
    color: #000000 !important;
}

.stChatMessage p,
.stChatMessage span,
.stChatMessage div {
    color: #000000 !important;
}


/* ================================
   DARK BUTTONS
   ================================ */

.stButton > button {
    background: #ffffff !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
}

.stButton > button:hover {
    background: #ffffff !important;
    color: #ffffff !important;
}


/* ================================
   SOURCE CARD - WHITE BACKGROUND
   ================================ */

.source {
    background: #ffffff;
    border-left: 4px solid #2563eb;
    border-radius: 10px;
    padding: 12px 15px;
    margin: 8px 0;
    color: #000000 !important;
}

.source b {
    color: #000000 !important;
}

.source .small {
    color: #475569 !important;
}


/* ================================
   BADGES
   ================================ */

.badge {
    padding: 5px 9px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
}

.official {
    background: #dcfce7 !important;
    color: #166534 !important;
}

.secondary {
    background: #fef3c7 !important;
    color: #92400e !important;
}


/* ================================
   NORMAL TEXT
   ================================ */

.small {
    color: #475569 !important;
}


/* ================================
   CHAT INPUT
   ================================ */

[data-testid="stChatInput"] {
    background: #ffffff !important;
}

[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    color: #000000 !important;
}


/* ================================
   METRIC CARDS
   ================================ */

[data-testid="stMetric"] {
    background: #ffffff !important;
    border-radius: 12px;
    padding: 12px;
}

[data-testid="stMetric"] label {
    color: #475569 !important;
}

[data-testid="stMetricValue"] {
    color: #000000 !important;
}


/* ================================
   FILE UPLOADER
   ================================ */

[data-testid="stFileUploader"] {
    background: #ffffff !important;
    color: #000000 !important;
}

[data-testid="stFileUploader"] * {
    color: #000000 !important;
}


/* ================================
   EXPANDER
   ================================ */

[data-testid="stExpander"] {
    background: #ffffff !important;
    color: #000000 !important;
}

[data-testid="stExpander"] * {
    color: #000000 !important;
}


/* ================================
   WARNING / INFO / SUCCESS
   ================================ */

[data-testid="stAlert"] {
    color: #000000 !important;
}


/* ================================
   HEADINGS ON LIGHT BACKGROUND
   ================================ */

h1, h2, h3, h4, h5, h6 {
    color: #000000 !important;
}

</style>
""", unsafe_allow_html=True)




# =========================================================
# SESSION STATE
# =========================================================

if "universities" not in st.session_state:
    st.session_state.universities = load_universities()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

if "active_university" not in st.session_state:
    st.session_state.active_university = None


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🎓 CampusSolve AI")
    st.caption("Verified university information assistant")

    st.divider()

    # -----------------------------------------------------
    # UNIVERSITY INPUT
    # -----------------------------------------------------

    st.markdown("### 🏫 University")

    university_input = st.text_input(
        "Enter university name",
        placeholder="e.g. HSTU",
        key="university_input",
    )

    # -----------------------------------------------------
    # FIND UNIVERSITY
    # -----------------------------------------------------

    if st.button(
        "🔍 Find University",
        use_container_width=True,
    ):

        if not university_input.strip():

            st.warning(
                "Please enter a university name first."
            )

        else:

            university_name = university_input.strip()

            with st.spinner(
                f"Finding official website for {university_name}..."
            ):

                try:

                    result = discover_university(
                        university_name
                    )

                    if result.get("ok"):

                        university_data = result["university"]

                        # Save university
                        st.session_state.universities[
                            university_name
                        ] = university_data

                        save_universities(
                            st.session_state.universities
                        )

                        # Set active university
                        st.session_state.active_university = (
                            university_name
                        )

                        st.success(
                            "University found successfully."
                        )

                        st.rerun()

                    else:

                        st.error(
                            result.get(
                                "message",
                                "University could not be found.",
                            )
                        )

                except Exception as e:

                    st.error(
                        f"University search failed: {e}"
                    )

    # -----------------------------------------------------
    # SAVED UNIVERSITIES
    # -----------------------------------------------------

    saved_universities = list(
        st.session_state.universities.keys()
    )

    if saved_universities:

        st.markdown("### 📚 Saved Universities")

        saved_options = [
            "-- Select a saved university --"
        ] + saved_universities

        saved_selection = st.selectbox(
            "Choose university",
            saved_options,
            key="saved_university_selection",
        )

        if (
            saved_selection
            != "-- Select a saved university --"
        ):

            st.session_state.active_university = (
                saved_selection
            )

    # -----------------------------------------------------
    # ACTIVE UNIVERSITY
    # -----------------------------------------------------

    active_name = (
        st.session_state.active_university
    )

    if active_name:

        active_uni = st.session_state.universities.get(
            active_name
        )

        if active_uni:

            st.divider()

            st.markdown("### ✅ Active University")

            st.write(active_name)

            st.caption(
                f"Official domain: "
                f"{active_uni.get('domain', 'Unknown')}"
            )

    # -----------------------------------------------------
    # STUDENT CONTEXT
    # -----------------------------------------------------

    st.divider()

    st.markdown("### 👨‍🎓 Student Information")

    department = st.text_input(
        "🏷️ Department",
        placeholder="e.g. CSE",
        key="department",
    )

    level = st.selectbox(
        "📚 Level / Year",
        [
            
            "1st Year",
            "2nd Year",
            "3rd Year",
            "4th Year",
            "Masters",
            "PhD",
            "Any",
        ],
        key="level",
    )

    # -----------------------------------------------------
    # MANUAL UNIVERSITY INFORMATION
    # -----------------------------------------------------

    st.divider()

    with st.expander(
        "⚙️ Add / Update University Information"
    ):

        manual_url = st.text_input(
            "Official website",
            placeholder="https://example.edu.bd",
            key="manual_url",
        )

        manual_fb = st.text_input(
            "Official Facebook page",
            placeholder="https://facebook.com/...",
            key="manual_fb",
        )

        if st.button(
            "💾 Save University",
            use_container_width=True,
        ):

            if not university_input.strip():

                st.warning(
                    "Please enter the university name first."
                )

            else:

                university_name = (
                    university_input.strip()
                )

                with st.spinner(
                    "Saving university information..."
                ):

                    try:

                        result = discover_university(
                            university_name,
                            manual_url.strip(),
                            manual_fb.strip(),
                        )

                        if result.get("ok"):

                            st.session_state.universities[
                                university_name
                            ] = result["university"]

                            save_universities(
                                st.session_state.universities
                            )

                            st.session_state.active_university = (
                                university_name
                            )

                            st.success(
                                "University saved successfully."
                            )

                            st.rerun()

                        else:

                            st.error(
                                result.get(
                                    "message",
                                    "Could not save university.",
                                )
                            )

                    except Exception as e:

                        st.error(
                            f"Could not save university: {e}"
                        )

    # -----------------------------------------------------
    # SYSTEM STATUS
    # -----------------------------------------------------

    st.divider()

    st.markdown("### ⚙️ System Status")

    st.markdown("🟢 **Gemma AI** — Ready")
    st.markdown("🟢 **Live University Search** — Ready")
    st.markdown("🟢 **Source Verification** — Ready")
    st.markdown("🟢 **ElevenLabs Voice** — Ready")

    st.caption(
        "API keys are loaded from environment variables."
    )


# =========================================================
# MAIN HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🎓 CampusSolve AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-subtitle">
    Ask university-related questions and get answers
    based on official university sources.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CHECK ACTIVE UNIVERSITY
# =========================================================

active_name = st.session_state.active_university

if not active_name:

    st.info(
        "🏫 Enter a university name from the sidebar "
        "and click **Find University** to start."
    )

    st.stop()


uni = st.session_state.universities.get(
    active_name
)

if not uni:

    st.error(
        "The selected university information could not be loaded."
    )

    st.stop()


# =========================================================
# UNIVERSITY INFORMATION
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "University",
        active_name,
    )

with col2:
    st.metric(
        "Department",
        department if department else "Any",
    )

with col3:
    st.metric(
        "Level",
        level,
    )


st.divider()

st.markdown(
    f"### 🔎 Ask {active_name}"
)

st.write(
    "Questions are searched against the selected "
    "university's official sources first."
)


# =========================================================
# PREVIOUS CHAT MESSAGES
# =========================================================

for message in st.session_state.messages:

    role = message.get("role")

    content = message.get("content")

    with st.chat_message(role):

        if role == "assistant":

            # ---------------------------------------------
            # Structured answer
            # ---------------------------------------------

            if isinstance(content, dict):

                # Status
                status = content.get(
                    "status",
                    "verified",
                )

                if status == "verified":

                    st.success(
                        "Verified information"
                    )

                elif status == "partial":

                    st.warning(
                        "Partially verified information"
                    )

                elif status == "not_found":

                    st.warning(
                        "No valid official source found"
                    )

                # Main answer
                answer_text = content.get(
                    "answer",
                    "",
                )

                if answer_text:

                    st.markdown(
                        "#### 💬 Answer"
                    )

                    st.markdown(
                        answer_text
                    )

                # Key information
                key_information = content.get(
                    "key_information",
                    [],
                )

                if key_information:

                    st.markdown(
                        "#### 📌 Key Information"
                    )

                    for item in key_information:

                        st.markdown(
                            f"- {item}"
                        )

                # Steps
                steps = content.get(
                    "steps",
                    [],
                )

                if steps:

                    st.markdown(
                        "#### 📝 Steps"
                    )

                    for i, step in enumerate(
                        steps,
                        1,
                    ):

                        st.markdown(
                            f"{i}. {step}"
                        )

                # Notes
                notes = content.get(
                    "important_notes",
                    [],
                )

                if notes:

                    st.markdown(
                        "#### ⚠️ Important Notes"
                    )

                    for note in notes:

                        st.markdown(
                            f"- {note}"
                        )

            # ---------------------------------------------
            # Normal string answer
            # ---------------------------------------------

            else:

                st.markdown(
                    content
                )

        else:

            st.markdown(
                content
            )


# =========================================================
# QUESTION INPUT
# =========================================================

question = st.chat_input(
    "e.g. How many department in HSTU?"
)


# =========================================================
# PROCESS QUESTION
# =========================================================

if question:

    # -----------------------------------------------------
    # Add user message
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):

        st.markdown(
            question
        )

    # -----------------------------------------------------
    # Assistant response
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        status_box = st.status(
            "🔎 Searching official university sources...",
            expanded=True,
        )

        try:

            # =============================================
            # CONTEXT
            # =============================================

            context = (
                f"Department: "
                f"{department if department else 'Any'}\n"
                f"Level: {level}"
            )

            # =============================================
            # SEARCH UNIVERSITY SOURCES
            # =============================================

            raw_sources = search_university_sources(
                university=uni,
                question=question,
                department=department,
                level=level,
                max_results=10,
            )

            # =============================================
            # VERIFY / RANK SOURCES
            # =============================================

            sources = rank_and_verify_sources(
                raw_sources,
                uni,
            )

            st.session_state.last_sources = sources

            status_box.update(
                label=(
                    f"🔎 Found {len(sources)} "
                    f"candidate sources. "
                    f"Generating answer..."
                ),
                state="running",
            )

            # =============================================
            # GEMMA ANSWER
            # =============================================

            answer = answer_with_gemma(
                question=question,
                university=uni,
                context=context,
                sources=sources,
            )

            status_box.update(
                label="✅ Answer generated",
                state="complete",
            )

            # =============================================
            # DISPLAY ANSWER
            # =============================================

            st.markdown(
                "### 💬 Answer"
            )

            if isinstance(answer, dict):

                answer_text = answer.get(
                    "answer",
                    "",
                )

                if answer.get("status") == "verified":

                    st.success(
                        "Verified information"
                    )

                elif answer.get("status") == "partial":

                    st.warning(
                        "Partially verified information"
                    )

                elif answer.get("status") == "not_found":

                    st.warning(
                        "No valid official source found."
                    )

                if answer_text:

                    st.markdown(
                        answer_text
                    )

                # -----------------------------------------
                # Key information
                # -----------------------------------------

                key_information = answer.get(
                    "key_information",
                    [],
                )

                if key_information:

                    st.markdown(
                        "#### 📌 Key Information"
                    )

                    for item in key_information:

                        st.markdown(
                            f"- {item}"
                        )

                # -----------------------------------------
                # Steps
                # -----------------------------------------

                steps = answer.get(
                    "steps",
                    [],
                )

                if steps:

                    st.markdown(
                        "#### 📝 Steps"
                    )

                    for i, step in enumerate(
                        steps,
                        1,
                    ):

                        st.markdown(
                            f"{i}. {step}"
                        )

                # -----------------------------------------
                # Important notes
                # -----------------------------------------

                notes = answer.get(
                    "important_notes",
                    [],
                )

                if notes:

                    st.markdown(
                        "#### ⚠️ Important Notes"
                    )

                    for note in notes:

                        st.markdown(
                            f"- {note}"
                        )

                # Text for TTS
                tts_text = answer_text

            else:

                # Current llm.py returns string
                tts_text = str(answer)

                st.markdown(
                    tts_text
                )

            # =============================================
            # VERIFIED SOURCES
            # =============================================

            if sources:

                st.divider()

                st.markdown(
                    "### 📚 Sources"
                )

                # Show only first 6
                # to keep interface clean
                for i, source in enumerate(
                    sources[:6],
                    1,
                ):

                    title = source.get(
                        "title",
                        "Official Source",
                    )

                    url = source.get(
                        "url",
                        "",
                    )

                    tier = source.get(
                        "tier",
                        "Source",
                    )

                    date = source.get(
                        "published_date"
                    )

                    snippet = source.get(
                        "snippet",
                        "",
                    )

                    st.markdown(
                        f"**{i}. {title}**"
                    )

                    st.caption(
                        f"{tier}"
                    )

                    if date:

                        st.caption(
                            f"Date detected: {date}"
                        )

                    if snippet:

                        st.write(
                            snippet[:500]
                        )

                    if url:

                        st.markdown(
                            f"[🔗 Open source]({url})"
                        )

                    st.divider()

            else:

                st.info(
                    "No candidate sources were returned."
                )

            # =============================================
            # TEXT TO SPEECH
            # =============================================

            st.markdown(
                "### 🔊 Voice"
            )

            if st.button(
                "🔊 Speak Answer",
                key=f"tts_{len(st.session_state.messages)}",
            ):

                audio = text_to_speech(
                    tts_text
                )

                if audio:

                    st.audio(
                        audio,
                        format="audio/mp3",
                    )

                else:

                    st.warning(
                        "ElevenLabs could not generate audio. "
                        "Please check your API key and settings."
                    )

            # =============================================
            # SAVE ASSISTANT MESSAGE
            # =============================================

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

        # =================================================
        # ERROR HANDLING
        # =================================================

        except Exception as e:

            status_box.update(
                label="❌ Search failed",
                state="error",
            )

            st.error(
                f"Could not complete the request: {e}"
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "CampusSolve AI searches university-specific sources "
    "and does not intentionally invent deadlines, fees, "
    "procedures, or official instructions."
)