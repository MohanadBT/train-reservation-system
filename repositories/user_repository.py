"""
repositories/user_repository.py
--------------------------------
Data Access Layer - handles all database operations for users.
No business logic here — just raw SQL queries.
"""

from database.db import get_connection
from models.entities import User


def find_by_username(username: str) -> User | None:
    """Returns a User object matching the username, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_user(row)


def find_by_id(user_id: int) -> User | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return _row_to_user(row) if row else None


def get_all() -> list[User]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [_row_to_user(r) for r in rows]


def create(username, password_hash, full_name, email, phone_number, role) -> int:
    """Inserts a new user, returns the new row id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO users (username, password_hash, full_name, email, phone_number, role) VALUES (?,?,?,?,?,?)",
        (username, password_hash, full_name, email, phone_number, role)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update(user_id, full_name, email, phone_number, role):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET full_name=?, email=?, phone_number=?, role=? WHERE id=?",
        (full_name, email, phone_number, role, user_id)
    )
    conn.commit()
    conn.close()


def delete(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def _row_to_user(row) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
        full_name=row["full_name"],
        email=row["email"],
        phone_number=row["phone_number"],
        role=row["role"],
        created_at=row["created_at"],
    )
