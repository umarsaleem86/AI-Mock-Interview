import os
import json
import uuid
import sqlite3
import re

import bcrypt

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
except ImportError:
    psycopg2 = None
    RealDictCursor = None
    Json = None


def _get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def _using_postgres() -> bool:
    return bool(_get_database_url()) and psycopg2 is not None


def _dict_rows(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _dict_row(cursor):
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def _valid_email(email: str) -> bool:
    email = (email or "").strip().lower()
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def get_connection():
    database_url = _get_database_url()

    if database_url and psycopg2 is not None:
        return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

    conn = sqlite3.connect("interview_ai.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    if _using_postgres():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_verified BOOLEAN DEFAULT FALSE,
                verification_token VARCHAR(255),
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

    else:
        cur.execute("PRAGMA foreign_keys = ON")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_verified INTEGER DEFAULT 0,
                verification_token TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                seniority TEXT,
                demo_mode INTEGER DEFAULT 0,
                cv_text TEXT,
                jd_text TEXT,
                questions TEXT,
                answers TEXT,
                scores TEXT,
                tips TEXT,
                justifications TEXT,
                report TEXT,
                avg_score REAL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

    conn.commit()
    cur.close()
    conn.close()


def create_session(user_id: int) -> str:
    token = uuid.uuid4().hex
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if _using_postgres():
            cur.execute(
                "INSERT INTO sessions (token, user_id) VALUES (%s, %s)",
                (token, user_id),
            )
        else:
            cur.execute(
                "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
                (token, user_id),
            )

        conn.commit()
        return token

    except Exception:
        if conn:
            conn.rollback()
        return ""

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_session(token: str) -> dict:
    if not token:
        return {}

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if _using_postgres():
            cur.execute("""
                SELECT s.user_id, u.email
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = %s
            """, (token,))
            row = cur.fetchone()
        else:
            cur.execute("""
                SELECT s.user_id, u.email
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ?
            """, (token,))
            row = _dict_row(cur)

        if row:
            return {
                "user_id": row["user_id"],
                "email": row["email"],
                "username": row["email"],
            }

        return {}

    except Exception:
        return {}

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def delete_session(token: str):
    if not token:
        return

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if _using_postgres():
            cur.execute("DELETE FROM sessions WHERE token = %s", (token,))
        else:
            cur.execute("DELETE FROM sessions WHERE token = ?", (token,))

        conn.commit()

    except Exception:
        if conn:
            conn.rollback()

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def create_user(email: str, password: str, verification_token: str = "") -> dict:
    email = (email or "").strip().lower()

    if not _valid_email(email):
        return {"success": False, "error": "Please enter a valid email address"}

    if len(password or "") < 6:
        return {"success": False, "error": "Password must be at least 6 characters"}

    if not verification_token:
        verification_token = uuid.uuid4().hex

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if _using_postgres():
            cur.execute("""
                INSERT INTO users (
                    email, password_hash, is_verified, verification_token
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id, email, is_verified, verification_token
            """, (email, password_hash, False, verification_token))
            user = cur.fetchone()

        else:
            cur.execute("""
                INSERT INTO users (
                    email, password_hash, is_verified, verification_token
                )
                VALUES (?, ?, ?, ?)
            """, (email, password_hash, 0, verification_token))

            user_id = cur.lastrowid
            cur.execute("""
                SELECT id, email, is_verified, verification_token
                FROM users
                WHERE id = ?
            """, (user_id,))
            user = _dict_row(cur)

        conn.commit()

        return {
            "success": True,
            "user_id": user["id"],
            "email": user["email"],
            "username": user["email"],
            "is_verified": bool(user["is_verified"]),
            "verification_token": user["verification_token"],
        }

    except Exception as e:
        if conn:
            conn.rollback()

        message = str(e).lower()
        if "unique" in message or "duplicate key" in message:
            return {"success": False, "error": "An account with this email already exists"}

        return {"success": False, "error": str(e)}

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def verify_email_token(token: str) -> dict:
    token = (token or "").strip()

    if not token:
        return {"success": False, "error": "Invalid verification link"}

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if _using_postgres():
            cur.execute("""
                UPDATE users
                SET is_verified = TRUE,
                    verification_token = NULL
                WHERE verification_token = %s
                RETURNING id, email
            """, (token,))
            user = cur.fetchone()

        else:
            cur.execute("""
                SELECT id, email
                FROM users
                WHERE verification_token = ?
            """, (token,))
            user = _dict_row(cur)

            if user:
                cur.execute("""
                    UPDATE users
                    SET is_verified = 1,
                        verification_token = NULL
                    WHERE verification_token = ?
                """, (token,))

        conn.commit()

        if not user:
            return {
                "success": False,
                "error": "Verification link is invalid or already used"
            }

        return {
            "success": True,
            "user_id": user["id"],
            "email": user["email"],
            "username": user["email"],
        }

    except Exception as e:
        if conn:
            conn.rollback()
        return {"success": False, "error": str(e)}

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def verify_user(email: str, password: str) -> dict:
    email = (email or "").strip().lower()

    if not _valid_email(email):
        return {"success": False, "error": "Please enter a valid email address"}

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if _using_postgres():
            cur.execute("""
                SELECT id, email, password_hash, is_verified
                FROM users
                WHERE email = %s
            """, (email,))
            user = cur.fetchone()

        else:
            cur.execute("""
                SELECT id, email, password_hash, is_verified
                FROM users
                WHERE email = ?
            """, (email,))
            user = _dict_row(cur)

        if not user:
            return {"success": False, "error": "Invalid email or password"}

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        ):
            return {"success": False, "error": "Invalid email or password"}

        if not bool(user["is_verified"]):
            return {
                "success": False,
                "error": "Please verify your email before logging in."
            }

        return {
            "success": True,
            "user_id": user["id"],
            "email": user["email"],
            "username": user["email"],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def save_interview(
    user_id: int,
    seniority: str,
    demo_mode: bool,
    cv_text: str,
    jd_text: str,
    questions: list,
    answers: list,
    scores: list,
    tips: list,
    justifications: list,
    report: str,
    avg_score: float,
) -> dict:
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if _using_postgres():
            cur.execute("""
                INSERT INTO interviews (
                    user_id, seniority, demo_mode, cv_text, jd_text,
                    questions, answers, scores, tips, justifications, report, avg_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id,
                seniority,
                demo_mode,
                cv_text,
                jd_text,
                Json(questions),
                Json(answers),
                Json(scores),
                Json(tips),
                Json(justifications),
                report,
                avg_score,
            ))
            result = cur.fetchone()
            interview_id = result["id"]

        else:
            cur.execute("""
                INSERT INTO interviews (
                    user_id, seniority, demo_mode, cv_text, jd_text,
                    questions, answers, scores, tips, justifications, report, avg_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                seniority,
                int(demo_mode),
                cv_text,
                jd_text,
                json.dumps(questions),
                json.dumps(answers),
                json.dumps(scores),
                json.dumps(tips),
                json.dumps(justifications),
                report,
                avg_score,
            ))
            interview_id = cur.lastrowid

        conn.commit()
        return {"success": True, "interview_id": interview_id}

    except Exception as e:
        if conn:
            conn.rollback()
        return {"success": False, "error": str(e)}

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_all_interviews_admin() -> list:
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT i.id, u.email, i.created_at, i.seniority, i.demo_mode,
                   i.cv_text, i.jd_text, i.questions, i.answers, i.scores,
                   i.tips, i.justifications, i.report, i.avg_score
            FROM interviews i
            JOIN users u ON i.user_id = u.id
            ORDER BY i.created_at DESC
        """)

        if _using_postgres():
            rows = cur.fetchall()
        else:
            rows = _dict_rows(cur)

        for row in rows:
            row["username"] = row.get("email", "")

        return rows

    except Exception:
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_all_users_admin() -> list:
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if _using_postgres():
            cur.execute("""
                SELECT u.id, u.email, u.is_verified, u.created_at,
                       COUNT(i.id) AS interview_count,
                       ROUND(AVG(i.avg_score)::numeric, 2) AS avg_score
                FROM users u
                LEFT JOIN interviews i ON i.user_id = u.id
                GROUP BY u.id, u.email, u.is_verified, u.created_at
                ORDER BY u.created_at DESC
            """)
            rows = cur.fetchall()

        else:
            cur.execute("""
                SELECT u.id, u.email, u.is_verified, u.created_at,
                       COUNT(i.id) AS interview_count,
                       ROUND(AVG(i.avg_score), 2) AS avg_score
                FROM users u
                LEFT JOIN interviews i ON i.user_id = u.id
                GROUP BY u.id, u.email, u.is_verified, u.created_at
                ORDER BY u.created_at DESC
            """)
            rows = _dict_rows(cur)

        for row in rows:
            row["username"] = row.get("email", "")

        return rows

    except Exception:
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_user_interviews(user_id: int) -> list:
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if _using_postgres():
            cur.execute("""
                SELECT id, created_at, seniority, demo_mode, avg_score,
                       questions, answers, scores, tips, justifications, report
                FROM interviews
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            interviews = cur.fetchall()

        else:
            cur.execute("""
                SELECT id, created_at, seniority, demo_mode, avg_score,
                       questions, answers, scores, tips, justifications, report
                FROM interviews
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            interviews = _dict_rows(cur)

        return interviews

    except Exception:
        return []

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
