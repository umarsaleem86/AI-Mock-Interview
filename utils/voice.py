"""
Voice utilities for text-to-speech and speech-to-text functionality.
Uses Replit AI Integrations for OpenAI audio capabilities.
"""

import io
import os
import base64
from typing import Tuple, Optional
from openai import OpenAI
import streamlit as st

from config import TTS_VOICE


def get_openai_client() -> OpenAI:
    """
    Get OpenAI client configured for Replit AI Integrations.
    This uses Replit's AI Integrations service, which provides OpenAI-compatible 
    API access without requiring your own OpenAI API key.
    """
    return OpenAI(
        api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
        base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    )


def text_to_speech(text: str) -> Tuple[Optional[bytes], str]:
    """
    Convert text to speech using gpt-audio model.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Tuple of (audio_bytes, error_message)
    """
    try:
        client = get_openai_client()
        
        response = client.chat.completions.create(
            model="gpt-audio",
            modalities=["text", "audio"],
            audio={"voice": TTS_VOICE, "format": "wav"},
            messages=[
                {"role": "system", "content": "You are an assistant that performs text-to-speech."},
                {"role": "user", "content": f"Repeat the following text verbatim: {text}"},
            ],
        )
        
        audio_data = getattr(response.choices[0].message, "audio", None)
        if audio_data and hasattr(audio_data, "data"):
            audio_bytes = base64.b64decode(audio_data.data)
            return audio_bytes, ""
        
        return None, "No audio data received from TTS"
        
    except Exception as e:
        return None, f"Text-to-speech failed: {str(e)}"


def speech_to_text(audio_bytes: bytes, file_format: str = "wav") -> Tuple[str, str]:
    """
    Convert speech to text using gpt-audio model.
    
    Args:
        audio_bytes: Raw audio bytes
        file_format: Audio file format (wav, mp3, etc.)
        
    Returns:
        Tuple of (transcribed_text, error_message)
    """
    try:
        client = get_openai_client()
        
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        response = client.chat.completions.create(
            model="gpt-audio",
            modalities=["text"],
            messages=[
                {"role": "system", "content": "You are an assistant that performs speech-to-text. Transcribe the audio exactly as spoken."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Transcribe the following audio exactly as spoken."},
                        {"type": "input_audio", "input_audio": {"data": audio_base64, "format": file_format}},
                    ],
                },
            ],
        )
        
        text = response.choices[0].message.content or ""
        text = text.strip()
        
        if not text:
            return "", "Could not transcribe audio. Please try recording again with clearer speech."
        
        return text, ""
        
    except Exception as e:
        return "", f"Transcription failed: {str(e)}. Please try recording again."


def play_audio(audio_bytes: bytes):
    """
    Play audio in Streamlit using st.audio.
    
    Args:
        audio_bytes: Audio data in bytes
    """
    st.audio(audio_bytes, format="audio/wav", autoplay=True)
