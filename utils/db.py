import os
import json
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from datetime import datetime


def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT NOW(),
            seniority VARCHAR(20),
            demo_mode BOOLEAN DEFAULT FALSE,
            cv_text TEXT,
            jd_text TEXT,
            questions JSONB,
            answers JSONB,
            scores JSONB,
            tips JSONB,
            justifications JSONB,
            report TEXT,
            avg_score FLOAT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token VARCHAR(64) PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def create_session(user_id: int) -> str:
    token = uuid.uuid4().hex
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO sessions (token, user_id) VALUES (%s, %s)", (token, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return token
    except Exception:
        return ""


def get_session(token: str) -> dict:
    if not token:
        return {}
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT s.user_id, u.username FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = %s
        """, (token,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return {"user_id": row["user_id"], "username": row["username"]}
        return {}
    except Exception:
        return {}


def delete_session(token: str):
    if not token:
        return
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM sessions WHERE token = %s", (token,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


def create_user(username: str, password: str) -> dict:
    username = username.strip().lower()
    if len(username) < 3:
        return {"success": False, "error": "Username must be at least 3 characters"}
    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters"}

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, username",
            (username, password_hash)
        )
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True, "user_id": user["id"], "username": user["username"]}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        return {"success": False, "error": "Username already taken"}
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return {"success": False, "error": str(e)}


def verify_user(username: str, password: str) -> dict:
    username = username.strip().lower()
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            return {"success": False, "error": "Invalid username or password"}

        if bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
            return {"success": True, "user_id": user["id"], "username": user["username"]}
        else:
            return {"success": False, "error": "Invalid username or password"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_interview(user_id: int, seniority: str, demo_mode: bool, cv_text: str, jd_text: str,
                   questions: list, answers: list, scores: list, tips: list,
                   justifications: list, report: str, avg_score: float) -> dict:
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO interviews (user_id, seniority, demo_mode, cv_text, jd_text,
                                    questions, answers, scores, tips, justifications, report, avg_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, seniority, demo_mode, cv_text, jd_text,
              json.dumps(questions), json.dumps(answers), json.dumps(scores),
              json.dumps(tips), json.dumps(justifications), report, avg_score))
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"success": True, "interview_id": result["id"]}
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return {"success": False, "error": str(e)}


def get_all_interviews_admin() -> list:
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT i.id, u.username, i.created_at, i.seniority, i.demo_mode,
                   i.cv_text, i.jd_text, i.questions, i.answers, i.scores,
                   i.tips, i.justifications, i.report, i.avg_score
            FROM interviews i
            JOIN users u ON i.user_id = u.id
            ORDER BY i.created_at DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception:
        return []


def get_all_users_admin() -> list:
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT u.id, u.username, u.created_at,
                   COUNT(i.id) AS interview_count,
                   ROUND(AVG(i.avg_score)::numeric, 2) AS avg_score
            FROM users u
            LEFT JOIN interviews i ON i.user_id = u.id
            GROUP BY u.id, u.username, u.created_at
            ORDER BY u.created_at DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception:
        return []


def get_user_interviews(user_id: int) -> list:
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, created_at, seniority, demo_mode, avg_score,
                   questions, answers, scores, tips, justifications, report
            FROM interviews
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        interviews = cur.fetchall()
        cur.close()
        conn.close()
        return interviews
    except Exception:
        return []
