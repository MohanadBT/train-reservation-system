"""
repositories/passenger_repository.py
--------------------------------------
Data Access Layer - handles all DB operations for passengers.
"""

from database.db import get_connection
from models.entities import Passenger


def get_all() -> list[Passenger]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM passengers ORDER BY full_name").fetchall()
    conn.close()
    return [_row_to_passenger(r) for r in rows]


def find_by_id(passenger_id: int) -> Passenger | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM passengers WHERE id=?", (passenger_id,)).fetchone()
    conn.close()
    return _row_to_passenger(row) if row else None


def search(query: str) -> list[Passenger]:
    """Search by name, email, or phone."""
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM passengers WHERE full_name LIKE ? OR email LIKE ? OR phone_number LIKE ?",
        (like, like, like)
    ).fetchall()
    conn.close()
    return [_row_to_passenger(r) for r in rows]


def create(full_name, id_number, email, phone_number) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO passengers (full_name, id_number, email, phone_number) VALUES (?,?,?,?)",
        (full_name, id_number, email, phone_number)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update(passenger_id, full_name, id_number, email, phone_number):
    conn = get_connection()
    conn.execute(
        "UPDATE passengers SET full_name=?, id_number=?, email=?, phone_number=? WHERE id=?",
        (full_name, id_number, email, phone_number, passenger_id)
    )
    conn.commit()
    conn.close()


def delete(passenger_id):
    conn = get_connection()
    conn.execute("DELETE FROM passengers WHERE id=?", (passenger_id,))
    conn.commit()
    conn.close()


def _row_to_passenger(row) -> Passenger:
    return Passenger(
        id=row["id"],
        full_name=row["full_name"],
        id_number=row["id_number"],
        email=row["email"],
        phone_number=row["phone_number"],
        created_at=row["created_at"],
    )
