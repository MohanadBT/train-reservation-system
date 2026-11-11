"""
security/hardening.py
---------------------
Session cookie settings and HTTP security headers.

- HttpOnly cookie      : JavaScript cannot read the session cookie (limits XSS damage)
- SameSite=Lax cookie  : browser does not send it on cross-site POSTs (extra CSRF defence)
- Secure cookie        : only sent over HTTPS (enable with COOKIE_SECURE=1 when deployed with HTTPS)
- 30 min session limit : idle sessions expire
- Security headers     : stop clickjacking, MIME sniffing, and restrict where content may load from
- no-store on logged-in pages so passenger data is not kept in the browser cache
"""

import os
from datetime import timedelta

from flask import session


def init_hardening(app) -> None:
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        MAX_CONTENT_LENGTH=1 * 1024 * 1024,  # reject request bodies over 1 MB
    )

    @app.after_request
    def _add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        # The templates use inline <style> and one inline <script>, so 'unsafe-inline'
        # is still needed here. Everything else is limited to our own origin.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; frame-ancestors 'none'; form-action 'self'"
        )
        if "user_id" in session:
            response.headers["Cache-Control"] = "no-store"
        return response
