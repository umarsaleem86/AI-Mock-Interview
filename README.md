# AI Mock Interview Platform

An AI-powered mock interview platform with full voice mode. The AI speaks questions and users answer by voice recording.

This app uses Replit AI Integrations for OpenAI access - no API key required! Charges are billed to your Replit credits.

## Features

- **Voice Mode**: AI speaks questions using text-to-speech, users respond via audio recording
- **Document Parsing**: Upload CV/Resume in PDF, Word (.docx), or text format
- **Instant Scoring**: Get scored 0-10 on each answer with justification
- **Pro Tips**: Actionable advice after each response
- **Final Report**: Comprehensive feedback with strengths, improvements, and 7-day practice plan

## Usage

1. **Upload CV**: Upload your resume (PDF, Word, or text file)
2. **Add Job Description** (Optional): Paste the job description for tailored questions
3. **Select Seniority**: Choose Junior/Mid/Senior level
4. **Start Interview**: Click to begin the voice interview
5. **Record Answers**: Click the microphone to record your responses
6. **Review & Submit**: Check transcription and submit your answer
7. **Get Feedback**: After 5 questions, generate a comprehensive report

## Project Structure

```
├── app.py                    # Main Streamlit application
├── config.py                 # Centralized configuration
├── utils/
│   ├── __init__.py
│   ├── pdf_parser.py         # Document parsing (PDF, Word, TXT)
│   ├── voice.py              # TTS and STT functionality
│   └── interview_engine.py   # OpenAI interview logic
└── README.md                 # This file
```

## Technologies

- **Streamlit**: Web application framework
- **OpenAI GPT-5-mini**: Interview question generation and evaluation
- **OpenAI gpt-audio**: Text-to-speech and speech-to-text
- **audio-recorder-streamlit**: Browser-based audio recording
