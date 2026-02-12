"""
AI Mock Interview Platform
Main Streamlit application with voice-enabled interview functionality.
"""

import json
import streamlit as st
from audio_recorder_streamlit import audio_recorder

from config import SENIORITY_LEVELS, TOTAL_QUESTIONS
from utils.pdf_parser import parse_document
from utils.voice import text_to_speech, speech_to_text, play_audio
from utils.interview_engine import (
    get_first_question,
    evaluate_answer_and_get_next,
    generate_final_report
)
from utils.db import init_db, create_user, verify_user, save_interview, get_user_interviews


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'logged_in': False,
        'user_id': None,
        'username': '',
        'page': 'interview',
        'cv_text': '',
        'jd_text': '',
        'messages': [],
        'current_question_index': 0,
        'questions': [],
        'answers': [],
        'scores': [],
        'tips': [],
        'justifications': [],
        'interview_started': False,
        'interview_completed': False,
        'voice_enabled': False,
        'demo_mode': True,
        'seniority': 'Mid',
        'current_audio': None,
        'awaiting_answer': False,
        'last_transcription': '',
        'show_transcription': False,
        'processing': False,
        'report_generated': False,
        'report_text': ''
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_interview():
    """Reset all interview-related session state."""
    st.session_state.messages = []
    st.session_state.current_question_index = 0
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.scores = []
    st.session_state.tips = []
    st.session_state.justifications = []
    st.session_state.interview_started = False
    st.session_state.interview_completed = False
    st.session_state.current_audio = None
    st.session_state.awaiting_answer = False
    st.session_state.last_transcription = ''
    st.session_state.show_transcription = False
    st.session_state.processing = False
    st.session_state.report_generated = False
    st.session_state.report_text = ''


def render_auth_page():
    """Render the login/register page."""
    st.title("🎯 AI Mock Interview Platform")
    st.markdown("Practice your interview skills with an AI interviewer!")

    st.markdown("---")

    tab_login, tab_register = st.tabs(["Login", "Create Account"])

    with tab_login:
        st.subheader("Login to Your Account")
        login_username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

        if st.button("Login", type="primary", use_container_width=True, key="login_btn"):
            if login_username and login_password:
                result = verify_user(login_username, login_password)
                if result["success"]:
                    st.session_state.logged_in = True
                    st.session_state.user_id = result["user_id"]
                    st.session_state.username = result["username"]
                    st.rerun()
                else:
                    st.error(result["error"])
            else:
                st.warning("Please enter both username and password")

    with tab_register:
        st.subheader("Create a New Account")
        reg_username = st.text_input("Choose a Username", key="reg_username", placeholder="At least 3 characters")
        reg_password = st.text_input("Choose a Password", type="password", key="reg_password", placeholder="At least 6 characters")
        reg_password2 = st.text_input("Confirm Password", type="password", key="reg_password2", placeholder="Re-enter your password")

        if st.button("Create Account", type="primary", use_container_width=True, key="register_btn"):
            if not reg_username or not reg_password:
                st.warning("Please fill in all fields")
            elif reg_password != reg_password2:
                st.error("Passwords do not match")
            else:
                result = create_user(reg_username, reg_password)
                if result["success"]:
                    st.session_state.logged_in = True
                    st.session_state.user_id = result["user_id"]
                    st.session_state.username = result["username"]
                    st.success("Account created! Redirecting...")
                    st.rerun()
                else:
                    st.error(result["error"])


def render_sidebar():
    """Render the sidebar with user inputs."""
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.username}")

        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.button("🎯 Interview", use_container_width=True):
                st.session_state.page = 'interview'
                st.rerun()
        with col_nav2:
            if st.button("📜 History", use_container_width=True):
                st.session_state.page = 'history'
                st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()

        if st.session_state.page == 'interview':
            render_interview_sidebar()


def render_interview_sidebar():
    """Render interview setup controls in sidebar."""
    st.header("📄 Interview Setup")

    st.subheader("Upload Your CV/Resume")
    uploaded_file = st.file_uploader(
        "Supported formats: PDF, Word (.docx), Text (.txt)",
        type=['pdf', 'docx', 'txt'],
        key='cv_upload'
    )

    if uploaded_file:
        cv_text, error = parse_document(uploaded_file)
        if error:
            st.error(f"⚠️ {error}")
            st.info("💡 Tips:\n- Ensure your PDF has selectable text (not scanned images)\n- Try saving as .docx or .txt if issues persist")
        else:
            st.session_state.cv_text = cv_text
            st.success(f"✅ CV loaded ({len(cv_text.split())} words)")

    st.divider()

    st.subheader("Job Description (Optional)")
    jd_text = st.text_area(
        "Paste the job description here",
        value=st.session_state.jd_text,
        height=150,
        placeholder="Paste job requirements, responsibilities, and qualifications..."
    )
    st.session_state.jd_text = jd_text

    st.divider()

    st.subheader("Settings")
    seniority = st.selectbox(
        "Seniority Level",
        SENIORITY_LEVELS,
        index=SENIORITY_LEVELS.index(st.session_state.seniority)
    )
    st.session_state.seniority = seniority

    voice_enabled = st.toggle("🔊 Voice Mode", value=st.session_state.voice_enabled)
    st.session_state.voice_enabled = voice_enabled

    demo_mode = st.toggle("🧪 Demo Mode (No AI Cost)", value=st.session_state.demo_mode)
    st.session_state.demo_mode = demo_mode

    if demo_mode:
        st.caption("✅ Demo mode uses mock responses - no API costs!")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        start_disabled = not st.session_state.cv_text or st.session_state.interview_started
        if st.button("▶️ Start Interview", disabled=start_disabled, use_container_width=True):
            start_interview()

    with col2:
        if st.button("🔄 Restart", use_container_width=True):
            reset_interview()
            st.rerun()

    if not st.session_state.cv_text:
        st.info("👆 Please upload your CV to begin")

    st.divider()
    st.caption("💡 **Tips:**\n- Speak clearly when recording\n- Take your time to think\n- Be specific with examples")


def start_interview():
    """Initialize and start the interview."""
    reset_interview()
    st.session_state.interview_started = True

    try:
        result = get_first_question(
            st.session_state.cv_text,
            st.session_state.jd_text,
            st.session_state.seniority,
            demo_mode=st.session_state.demo_mode
        )

        greeting = result.get('greeting', 'Welcome to your mock interview!')
        first_question = result.get('question', 'Tell me about yourself.')

        full_message = f"{greeting}\n\n**Question 1/{TOTAL_QUESTIONS}:**\n{first_question}"

        st.session_state.messages.append({
            'role': 'assistant',
            'content': full_message
        })
        st.session_state.questions.append(first_question)
        st.session_state.current_question_index = 1
        st.session_state.awaiting_answer = True

        if st.session_state.voice_enabled:
            audio_bytes, error = text_to_speech(full_message.replace('**', '').replace('\n\n', '. '))
            if not error:
                st.session_state.current_audio = audio_bytes

    except Exception as e:
        st.error(f"Failed to start interview: {str(e)}")
        st.session_state.interview_started = False


def process_answer(transcription: str):
    """Process the user's answer and get AI feedback."""
    st.session_state.processing = True

    st.session_state.messages.append({
        'role': 'user',
        'content': transcription
    })
    st.session_state.answers.append(transcription)

    conversation_history = []
    for msg in st.session_state.messages[:-1]:
        conversation_history.append({
            'role': msg['role'],
            'content': msg['content']
        })

    try:
        result = evaluate_answer_and_get_next(
            st.session_state.cv_text,
            st.session_state.jd_text,
            st.session_state.seniority,
            conversation_history,
            transcription,
            st.session_state.current_question_index,
            demo_mode=st.session_state.demo_mode
        )

        score = result.get('score', 5)
        justification = result.get('justification', '')
        pro_tip = result.get('pro_tip', '')
        next_question = result.get('next_question')

        st.session_state.scores.append(score)
        st.session_state.tips.append(pro_tip)
        st.session_state.justifications.append(justification)

        feedback_message = f"**Score: {score}/10**\n\n{justification}\n\n💡 **Pro Tip:** {pro_tip}"

        if next_question and st.session_state.current_question_index < TOTAL_QUESTIONS:
            st.session_state.current_question_index += 1
            feedback_message += f"\n\n---\n\n**Question {st.session_state.current_question_index}/{TOTAL_QUESTIONS}:**\n{next_question}"
            st.session_state.questions.append(next_question)
            st.session_state.awaiting_answer = True
        else:
            st.session_state.interview_completed = True
            st.session_state.awaiting_answer = False
            feedback_message += "\n\n---\n\n🎉 **Interview Complete!** Click 'Generate Feedback' below to get your detailed report."

        st.session_state.messages.append({
            'role': 'assistant',
            'content': feedback_message
        })

    except Exception as e:
        st.session_state.messages.append({
            'role': 'assistant',
            'content': f"⚠️ There was an error evaluating your response. Please try again.\n\nError: {str(e)}"
        })
        st.session_state.answers.pop()
        st.session_state.awaiting_answer = True

    finally:
        st.session_state.processing = False


def render_chat():
    """Render the chat interface."""
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])


def render_response_input():
    """Render the response input controls."""
    if st.session_state.processing:
        st.markdown("---")
        st.spinner("Processing your answer...")
        return

    if not st.session_state.awaiting_answer:
        return

    st.markdown("---")
    st.markdown("### ✍️ Your Response")
    st.markdown(f"**Question {st.session_state.current_question_index} of {TOTAL_QUESTIONS}**")

    answer_key = f"answer_{st.session_state.current_question_index}_{len(st.session_state.answers)}"

    text_answer = st.text_area(
        "Type your answer here",
        key=answer_key,
        height=150,
        placeholder="Take your time and provide a detailed response..."
    )

    submit_key = f"submit_{st.session_state.current_question_index}_{len(st.session_state.answers)}"

    if st.button("📤 Submit Answer", type="primary", key=submit_key):
        if text_answer.strip():
            with st.spinner("Evaluating your response..."):
                process_answer(text_answer)
            st.rerun()
        else:
            st.warning("Please enter your answer before submitting.")


def render_final_report():
    """Render the final feedback report section."""
    if not st.session_state.interview_completed:
        return

    st.markdown("---")

    if st.session_state.report_generated:
        st.markdown("## 📋 Your Interview Feedback Report")
        avg_score = sum(st.session_state.scores) / len(st.session_state.scores)
        cols = st.columns(3)
        with cols[0]:
            st.metric("Average Score", f"{avg_score:.1f}/10")
        with cols[1]:
            st.metric("Questions Answered", len(st.session_state.answers))
        with cols[2]:
            performance = "Excellent" if avg_score >= 8 else "Good" if avg_score >= 6 else "Needs Work"
            st.metric("Performance", performance)
        st.markdown("---")
        st.markdown(st.session_state.report_text)
        st.success("This interview has been saved to your history.")
        return

    if st.button("📊 Generate Feedback Report", type="primary", use_container_width=True):
        with st.spinner("Generating your personalized feedback report..."):
            try:
                report = generate_final_report(
                    st.session_state.cv_text,
                    st.session_state.jd_text,
                    st.session_state.seniority,
                    st.session_state.questions,
                    st.session_state.answers,
                    st.session_state.scores,
                    st.session_state.tips,
                    demo_mode=st.session_state.demo_mode
                )

                st.session_state.report_generated = True
                st.session_state.report_text = report

                avg_score = sum(st.session_state.scores) / len(st.session_state.scores)
                save_interview(
                    user_id=st.session_state.user_id,
                    seniority=st.session_state.seniority,
                    demo_mode=st.session_state.demo_mode,
                    cv_text=st.session_state.cv_text,
                    jd_text=st.session_state.jd_text,
                    questions=st.session_state.questions,
                    answers=st.session_state.answers,
                    scores=st.session_state.scores,
                    tips=st.session_state.tips,
                    justifications=st.session_state.justifications,
                    report=report,
                    avg_score=avg_score
                )

                st.rerun()

            except Exception as e:
                st.error(f"Failed to generate report: {str(e)}")


def render_history_page():
    """Render the interview history page."""
    st.title("📜 Interview History")
    st.markdown(f"Past interviews for **{st.session_state.username}**")
    st.markdown("---")

    interviews = get_user_interviews(st.session_state.user_id)

    if not interviews:
        st.info("No interviews yet. Go to the Interview page to start your first one!")
        return

    for i, interview in enumerate(interviews):
        created = interview["created_at"].strftime("%B %d, %Y at %I:%M %p") if interview["created_at"] else "Unknown"
        avg = interview["avg_score"] or 0
        mode = "Demo" if interview["demo_mode"] else "AI"
        label = f"**{created}** — Score: {avg:.1f}/10 — {interview['seniority']} level — {mode} Mode"

        with st.expander(label, expanded=(i == 0)):
            cols = st.columns(3)
            with cols[0]:
                st.metric("Average Score", f"{avg:.1f}/10")
            with cols[1]:
                st.metric("Seniority", interview["seniority"])
            with cols[2]:
                performance = "Excellent" if avg >= 8 else "Good" if avg >= 6 else "Needs Work"
                st.metric("Performance", performance)

            st.markdown("---")

            raw_q = interview["questions"]
            raw_a = interview["answers"]
            raw_s = interview["scores"]
            raw_t = interview["tips"]
            questions = raw_q if isinstance(raw_q, list) else (json.loads(raw_q) if isinstance(raw_q, str) else [])
            answers = raw_a if isinstance(raw_a, list) else (json.loads(raw_a) if isinstance(raw_a, str) else [])
            scores = raw_s if isinstance(raw_s, list) else (json.loads(raw_s) if isinstance(raw_s, str) else [])
            tips = raw_t if isinstance(raw_t, list) else (json.loads(raw_t) if isinstance(raw_t, str) else [])

            for j in range(len(questions)):
                st.markdown(f"**Question {j+1}:** {questions[j]}")
                if j < len(answers):
                    st.markdown(f"**Your Answer:** {answers[j]}")
                if j < len(scores):
                    st.markdown(f"**Score:** {scores[j]}/10")
                if j < len(tips):
                    st.markdown(f"💡 **Pro Tip:** {tips[j]}")
                st.markdown("---")

            if interview["report"]:
                st.markdown("### 📋 Feedback Report")
                st.markdown(interview["report"])


def render_interview_page():
    """Render the main interview page."""
    st.title("🎯 AI Mock Interview Platform")
    st.markdown("Practice your interview skills with an AI interviewer!")

    if not st.session_state.interview_started:
        st.markdown("---")
        st.markdown("""
        ### Welcome! 👋

        **How it works:**
        1. 📄 Upload your CV/Resume in the sidebar
        2. 📝 Optionally paste the job description
        3. ▶️ Click "Start Interview" to begin
        4. ✍️ Answer questions using text input
        5. 📊 Get instant feedback and a final report

        **Features:**
        - 📈 **Instant Scoring**: Get scored 0-10 on each answer
        - 💡 **Pro Tips**: Actionable advice after each response
        - 📋 **Final Report**: Comprehensive feedback with practice plan
        - 📜 **History**: All interviews saved to your account
        """)
    else:
        render_chat()
        render_response_input()
        render_final_report()


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="AI Mock Interview",
        page_icon="🎯",
        layout="wide"
    )

    init_db()
    init_session_state()

    if not st.session_state.logged_in:
        render_auth_page()
        return

    render_sidebar()

    if st.session_state.page == 'history':
        render_history_page()
    else:
        render_interview_page()


if __name__ == "__main__":
    main()
