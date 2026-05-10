-- ============================================================
-- Train Schedule and Reservation Management System
-- Database Schema (SQLite)
-- ============================================================

-- Users table (Staff + Admins)
-- Administrator inherits from StaffMember (role column handles this)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    phone_number TEXT,
    role TEXT NOT NULL CHECK(role IN ('admin', 'staff')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Trains table
CREATE TABLE IF NOT EXISTS trains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_number TEXT NOT NULL UNIQUE,   -- e.g. TR-110
    name TEXT,
    total_seats INTEGER NOT NULL DEFAULT 100,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Schedules table (a train can have many schedules)
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER NOT NULL,
    route TEXT NOT NULL,                 -- e.g. "City A -> City B"
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    ticket_price REAL NOT NULL DEFAULT 0.0,
    available_seats INTEGER NOT NULL,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'cancelled', 'completed')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (train_id) REFERENCES trains(id)
);

-- Passengers table
CREATE TABLE IF NOT EXISTS passengers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    id_number TEXT,                      -- national ID or passport
    email TEXT,
    phone_number TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Reservations table
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    passenger_id INTEGER NOT NULL,
    schedule_id INTEGER NOT NULL,
    seat_class TEXT NOT NULL CHECK(seat_class IN ('Economy', 'Business', 'First Class')),
    status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed', 'cancelled')),
    booking_reference TEXT NOT NULL UNIQUE,  -- e.g. BK-000123
    created_by INTEGER NOT NULL,             -- staff user id
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (passenger_id) REFERENCES passengers(id),
    FOREIGN KEY (schedule_id) REFERENCES schedules(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
