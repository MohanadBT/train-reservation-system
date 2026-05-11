"""
app.py
-------
Main entry point for the Train Schedule and Reservation Management System.
This file creates the Flask app, registers all blueprints (route modules),
and initializes the database on first run.

Run with:
    python app.py

Then open: http://127.0.0.1:5000
"""

import os
from flask import Flask
from database.db import init_db

# ── Create Flask app ───────────────────────────────────────────────────────────

app = Flask(__name__)

# Secret key is required for Flask sessions (stores login state).
# In production, use an environment variable for this!
app.secret_key = os.environ.get("SECRET_KEY", "train-system-dev-secret-2025")

# ── Register route blueprints ──────────────────────────────────────────────────
# Each blueprint handles a group of related URLs.

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.staff_routes import staff_bp

app.register_blueprint(auth_bp)    # handles /login, /logout
app.register_blueprint(admin_bp)   # handles /admin/*
app.register_blueprint(staff_bp)   # handles /staff/*

# ── Initialize database on startup ────────────────────────────────────────────

init_db()

# ── Run the development server ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Train Schedule & Reservation Management System")
    print("  Running at: http://127.0.0.1:5000")
    print("="*55 + "\n")
    port = int(os.environ.get("PORT", 5000))
app.run(debug=False, host="0.0.0.0", port=port)
