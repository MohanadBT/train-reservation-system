"""
repositories/schedule_repository.py
-------------------------------------
Data Access Layer - handles all DB operations for trains and schedules.
"""

from database.db import get_connection
from models.entities import Schedule, Train


# ── Train queries ──────────────────────────────────────────────────────────────

def get_all_trains() -> list[Train]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM trains ORDER BY train_number").fetchall()
    conn.close()
    return [Train(id=r["id"], train_number=r["train_number"], name=r["name"], total_seats=r["total_seats"]) for r in rows]


def create_train(train_number, name, total_seats) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO trains (train_number, name, total_seats) VALUES (?,?,?)",
        (train_number, name, total_seats)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def delete_train(train_id):
    conn = get_connection()
    conn.execute("DELETE FROM trains WHERE id=?", (train_id,))
    conn.commit()
    conn.close()


# ── Schedule queries ───────────────────────────────────────────────────────────

def get_all_schedules() -> list[Schedule]:
    """Returns schedules joined with train number for display."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, t.train_number
        FROM schedules s
        JOIN trains t ON s.train_id = t.id
        ORDER BY s.departure_time
    """).fetchall()
    conn.close()
    return [_row_to_schedule(r) for r in rows]


def get_active_schedules() -> list[Schedule]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, t.train_number
        FROM schedules s
        JOIN trains t ON s.train_id = t.id
        WHERE s.status = 'active'
        ORDER BY s.departure_time
    """).fetchall()
    conn.close()
    return [_row_to_schedule(r) for r in rows]


def find_by_id(schedule_id: int) -> Schedule | None:
    conn = get_connection()
    row = conn.execute("""
        SELECT s.*, t.train_number
        FROM schedules s
        JOIN trains t ON s.train_id = t.id
        WHERE s.id = ?
    """, (schedule_id,)).fetchone()
    conn.close()
    return _row_to_schedule(row) if row else None


def create_schedule(train_id, route, departure_time, arrival_time, ticket_price, available_seats) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO schedules (train_id, route, departure_time, arrival_time, ticket_price, available_seats) VALUES (?,?,?,?,?,?)",
        (train_id, route, departure_time, arrival_time, ticket_price, available_seats)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_schedule(schedule_id, route, departure_time, arrival_time, ticket_price, available_seats, status):
    conn = get_connection()
    conn.execute("""
        UPDATE schedules
        SET route=?, departure_time=?, arrival_time=?, ticket_price=?, available_seats=?, status=?
        WHERE id=?
    """, (route, departure_time, arrival_time, ticket_price, available_seats, status, schedule_id))
    conn.commit()
    conn.close()


def delete_schedule(schedule_id):
    conn = get_connection()
    conn.execute("DELETE FROM schedules WHERE id=?", (schedule_id,))
    conn.commit()
    conn.close()


def decrement_seat(schedule_id):
    """Reduces available_seats by 1. Called when a reservation is confirmed."""
    conn = get_connection()
    conn.execute(
        "UPDATE schedules SET available_seats = available_seats - 1 WHERE id=? AND available_seats > 0",
        (schedule_id,)
    )
    conn.commit()
    conn.close()


def increment_seat(schedule_id):
    """Restores 1 seat when a reservation is cancelled."""
    conn = get_connection()
    conn.execute(
        "UPDATE schedules SET available_seats = available_seats + 1 WHERE id=?",
        (schedule_id,)
    )
    conn.commit()
    conn.close()


def _row_to_schedule(row) -> Schedule:
    return Schedule(
        id=row["id"],
        train_id=row["train_id"],
        route=row["route"],
        departure_time=row["departure_time"],
        arrival_time=row["arrival_time"],
        ticket_price=row["ticket_price"],
        available_seats=row["available_seats"],
        status=row["status"],
        train_number=row["train_number"] if "train_number" in row.keys() else None,
    )
