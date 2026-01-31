# AI Mock Interview Platform

## Overview
An AI-powered mock interview platform using Streamlit and OpenAI with full voice mode. The AI speaks interview questions and users respond via audio recording.

This uses Replit AI Integrations for OpenAI access - no API key required. Charges are billed to Replit credits.

## Project Structure
```
├── app.py                    # Main Streamlit application
├── config.py                 # Centralized configuration (model, voice settings)
├── utils/
│   ├── __init__.py
│   ├── pdf_parser.py         # Document parsing (PDF, Word, TXT)
│   ├── voice.py              # TTS and STT functionality using gpt-audio
│   └── interview_engine.py   # OpenAI interview logic and prompts
├── .streamlit/
│   └── config.toml           # Streamlit server configuration
└── README.md                 # User documentation
```

## Key Features
- CV/Resume upload (PDF, Word, TXT)
- Job description input (optional)
- Voice-enabled interview (TTS for AI, STT for user)
- 5-question interview flow
- Instant scoring (0-10) with pro tips
- Comprehensive final feedback report

## Configuration
All model and voice settings are in `config.py`:
- `OPENAI_MODEL`: GPT model for interview logic (default: gpt-5-mini)
- `TTS_VOICE`: Voice for TTS (default: alloy)
- `TOTAL_QUESTIONS`: Number of interview questions (default: 5)

## Environment Variables (Auto-configured)
- `AI_INTEGRATIONS_OPENAI_API_KEY`: Set automatically by Replit AI Integrations
- `AI_INTEGRATIONS_OPENAI_BASE_URL`: Set automatically by Replit AI Integrations

## Running the App
```bash
streamlit run app.py --server.port 5000
```

## Session State
The app uses `st.session_state` to manage:
- `cv_text`, `jd_text`: Document content
- `messages`: Chat history
- `current_question_index`: Question number (1-5)
- `questions`, `answers`, `scores`, `tips`: Interview data
- `interview_started`, `interview_completed`: Flow flags
- `voice_enabled`: Voice mode toggle
