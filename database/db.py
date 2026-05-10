"""
database/db.py
--------------
Data Access Layer - handles all direct SQLite connections.
This is the ONLY file that talks to the database file.
All other layers go through this module.
"""

import sqlite3
import os

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), "train_system.db")


def get_connection():
    """
    Opens and returns a database connection.
    row_factory=sqlite3.Row lets us access columns by name (like a dict).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # enforce FK constraints
    return conn


def init_db():
    """
    Reads schema.sql and runs it to create all tables.
    Also seeds a default admin account if no users exist.
    Called once at app startup.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    conn = get_connection()

    with open(schema_path, "r") as f:
        conn.executescript(f.read())

    conn.commit()

    # Seed default admin if table is empty
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        _seed_default_data(conn)

    conn.close()
    print("[DB] Database initialized successfully.")


def _seed_default_data(conn):
    """
    Creates default admin + staff accounts and sample trains/schedules.
    ONLY runs once on first startup.
    """
    from werkzeug.security import generate_password_hash

    # Default accounts
    users = [
        ("admin", generate_password_hash("admin123"), "System Administrator", "admin@railway.com", None, "admin"),
        ("staff1", generate_password_hash("staff123"), "John Smith", "john@railway.com", "555-1001", "staff"),
    ]
    conn.executemany(
        "INSERT INTO users (username, password_hash, full_name, email, phone_number, role) VALUES (?,?,?,?,?,?)",
        users
    )

    # Sample trains
    trains = [
        ("TR-110", "Express North", 120),
        ("TR-205", "Central Link", 80),
        ("TR-318", "Southern Star", 150),
    ]
    conn.executemany("INSERT INTO trains (train_number, name, total_seats) VALUES (?,?,?)", trains)

    # Sample schedules
    schedules = [
        (1, "City A -> City B", "2025-06-01 08:30:00", "2025-06-01 11:00:00", 45.00, 95),
        (2, "City C -> City D", "2025-06-01 11:45:00", "2025-06-01 14:30:00", 38.50, 68),
        (3, "City A -> City E", "2025-06-01 15:00:00", "2025-06-01 19:00:00", 62.00, 109),
    ]
    conn.executemany(
        "INSERT INTO schedules (train_id, route, departure_time, arrival_time, ticket_price, available_seats) VALUES (?,?,?,?,?,?)",
        schedules
    )

    conn.commit()
    print("[DB] Default data seeded.")
    print("[DB]  Admin login  -> username: admin    | password: admin123")
    print("[DB]  Staff login  -> username: staff1   | password: staff123")
