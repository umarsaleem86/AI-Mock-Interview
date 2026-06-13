import os
import requests


RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv(
    "FROM_EMAIL",
    "AI Interview <no-reply@aiinterviewpractice.com.au>"
)
APP_BASE_URL = os.getenv(
    "APP_BASE_URL",
    "https://aiinterviewpractice.com.au"
)


def send_verification_email(email: str, token: str):
    verification_link = f"{APP_BASE_URL}/?verify={token}"

    payload = {
        "from": FROM_EMAIL,
        "to": [email],
        "subject": "Verify your AI Interview account",
        "html": f"""
        <h2>Welcome to AI Interview</h2>

        <p>Thanks for creating an account.</p>

        <p>Please click the button below to verify your email address:</p>

        <a href="{verification_link}"
           style="
           background:#4f46e5;
           color:white;
           padding:12px 20px;
           text-decoration:none;
           border-radius:6px;">
           Verify Email
        </a>

        <p>If you did not create this account, please ignore this email.</p>
        """
    }

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30
    )

    return response.status_code == 200
