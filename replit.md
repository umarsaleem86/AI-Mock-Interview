# AI Mock Interview Platform

## Overview
An AI-powered mock interview platform using Streamlit and OpenAI. Users create accounts, upload CVs, and practice with AI-generated interview questions. All interviews are saved to their account for tracking progress.

This uses Replit AI Integrations for OpenAI access - no API key required. Charges are billed to Replit credits.

## Project Structure
```
├── app.py                    # Main Streamlit application (auth, interview, history)
├── config.py                 # Centralized configuration (model, voice settings)
├── utils/
│   ├── __init__.py
│   ├── db.py                 # Database module (PostgreSQL - users, interviews)
│   ├── pdf_parser.py         # Document parsing (PDF, Word, TXT)
│   ├── voice.py              # TTS and STT functionality using gpt-audio
│   └── interview_engine.py   # OpenAI interview logic and prompts
├── .streamlit/
│   └── config.toml           # Streamlit server configuration
└── README.md                 # User documentation
```

## Key Features
- User authentication (register/login with hashed passwords)
- Interview history saved per user in PostgreSQL
- CV/Resume upload (PDF, Word, TXT)
- Job description input (optional)
- Demo Mode (mock responses, no AI cost)
- 2-question interview flow with instant scoring (0-10)
- Comprehensive final feedback report with 7-day practice plan
- Interview history viewer with full Q&A and reports

## Database
PostgreSQL (Replit built-in) with two tables:
- `users`: id, username (unique), password_hash (bcrypt), created_at
- `interviews`: id, user_id (FK), created_at, seniority, demo_mode, cv_text, jd_text, questions/answers/scores/tips/justifications (JSONB), report, avg_score

## Configuration
All model and voice settings are in `config.py`:
- `OPENAI_MODEL`: GPT model for interview logic (default: gpt-5-mini)
- `TTS_VOICE`: Voice for TTS (default: alloy)
- `TOTAL_QUESTIONS`: Number of interview questions (default: 2)

## Environment Variables (Auto-configured)
- `AI_INTEGRATIONS_OPENAI_API_KEY`: Set automatically by Replit AI Integrations
- `AI_INTEGRATIONS_OPENAI_BASE_URL`: Set automatically by Replit AI Integrations
- `DATABASE_URL`: PostgreSQL connection string (auto-configured)

## Running the App
```bash
streamlit run app.py --server.port 5000
```

## Session State
The app uses `st.session_state` to manage:
- `logged_in`, `user_id`, `username`: Auth state
- `page`: Current page (interview/history)
- `cv_text`, `jd_text`: Document content
- `messages`: Chat history
- `current_question_index`: Question number (1-2)
- `questions`, `answers`, `scores`, `tips`: Interview data
- `interview_started`, `interview_completed`: Flow flags
- `demo_mode`: Demo mode toggle (default: True)
- `report_generated`, `report_text`: Final report data
