"""
repositories/reservation_repository.py
----------------------------------------
Data Access Layer - handles all DB operations for reservations.
"""

import random
import string
from database.db import get_connection
from models.entities import Reservation


def _generate_reference() -> str:
    """Generates a unique booking reference like BK-A3F29."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"BK-{suffix}"


def get_all() -> list[Reservation]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT r.*,
               p.full_name AS passenger_name,
               t.train_number,
               s.route
        FROM reservations r
        JOIN passengers p ON r.passenger_id = p.id
        JOIN schedules s ON r.schedule_id = s.id
        JOIN trains t ON s.train_id = t.id
        ORDER BY r.created_at DESC
    """).fetchall()
    conn.close()
    return [_row_to_reservation(r) for r in rows]


def get_by_passenger(passenger_id: int) -> list[Reservation]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT r.*,
               p.full_name AS passenger_name,
               t.train_number,
               s.route
        FROM reservations r
        JOIN passengers p ON r.passenger_id = p.id
        JOIN schedules s ON r.schedule_id = s.id
        JOIN trains t ON s.train_id = t.id
        WHERE r.passenger_id = ?
        ORDER BY r.created_at DESC
    """, (passenger_id,)).fetchall()
    conn.close()
    return [_row_to_reservation(r) for r in rows]


def find_by_id(reservation_id: int) -> Reservation | None:
    conn = get_connection()
    row = conn.execute("""
        SELECT r.*,
               p.full_name AS passenger_name,
               t.train_number,
               s.route
        FROM reservations r
        JOIN passengers p ON r.passenger_id = p.id
        JOIN schedules s ON r.schedule_id = s.id
        JOIN trains t ON s.train_id = t.id
        WHERE r.id = ?
    """, (reservation_id,)).fetchone()
    conn.close()
    return _row_to_reservation(row) if row else None


def create(passenger_id, schedule_id, seat_class, created_by) -> int:
    """Inserts a new confirmed reservation."""
    ref = _generate_reference()
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO reservations (passenger_id, schedule_id, seat_class, status, booking_reference, created_by) VALUES (?,?,?,?,?,?)",
        (passenger_id, schedule_id, seat_class, "confirmed", ref, created_by)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def cancel(reservation_id):
    """Sets status to 'cancelled'."""
    conn = get_connection()
    conn.execute(
        "UPDATE reservations SET status='cancelled' WHERE id=?",
        (reservation_id,)
    )
    conn.commit()
    conn.close()


def count_today() -> int:
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM reservations WHERE DATE(created_at) = DATE('now') AND status='confirmed'"
    ).fetchone()[0]
    conn.close()
    return count


def count_cancellations_today() -> int:
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM reservations WHERE DATE(created_at) = DATE('now') AND status='cancelled'"
    ).fetchone()[0]
    conn.close()
    return count


def total_revenue() -> float:
    conn = get_connection()
    result = conn.execute("""
        SELECT COALESCE(SUM(s.ticket_price), 0)
        FROM reservations r
        JOIN schedules s ON r.schedule_id = s.id
        WHERE r.status = 'confirmed'
    """).fetchone()[0]
    conn.close()
    return round(result, 2)


def _row_to_reservation(row) -> Reservation:
    return Reservation(
        id=row["id"],
        passenger_id=row["passenger_id"],
        schedule_id=row["schedule_id"],
        seat_class=row["seat_class"],
        status=row["status"],
        booking_reference=row["booking_reference"],
        created_by=row["created_by"],
        created_at=row["created_at"],
        passenger_name=row["passenger_name"] if "passenger_name" in row.keys() else None,
        train_number=row["train_number"] if "train_number" in row.keys() else None,
        route=row["route"] if "route" in row.keys() else None,
    )
