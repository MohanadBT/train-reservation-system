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
# SECURITY: no hard-coded fallback any more. If SECRET_KEY is not set, a random
# key is generated for this run (sessions end when the server restarts).
_secret = os.environ.get("SECRET_KEY")
if not _secret:
    import secrets
    _secret = secrets.token_hex(32)
    print("[SECURITY] SECRET_KEY not set - using a random key for this run.")
app.secret_key = _secret

# ── Security layers (Phase 2) ─────────────────────────────────────────────────
from security.hardening import init_hardening
from security.csrf import init_csrf

init_hardening(app)   # secure cookies + HTTP security headers
init_csrf(app)        # CSRF token check on every POST

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
