import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "subscriptions.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id INTEGER PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def is_subscribed(user_id: int) -> bool:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM subscribers WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row is not None


def add_user(user_id: int):
    with _get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscribers (user_id) VALUES (?)", (user_id,)
        )
        conn.commit()


def remove_user(user_id: int):
    with _get_conn() as conn:
        conn.execute(
            "DELETE FROM subscribers WHERE user_id = ?", (user_id,)
        )
        conn.commit()


def list_users() -> list:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id FROM subscribers ORDER BY added_at DESC"
        ).fetchall()
        return [row[0] for row in rows]
