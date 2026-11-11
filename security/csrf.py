"""
security/csrf.py
----------------
CSRF (Cross-Site Request Forgery) protection.

Problem: the browser sends the session cookie automatically, so a malicious
web page could make a logged-in admin submit a form to our system
(e.g. delete a schedule) without the admin knowing.

Fix: every session gets a random token. Every POST/PUT/PATCH/DELETE request
must send the same token back (hidden form field "csrf_token" or the
"X-CSRF-Token" header). A third-party site cannot read our token, so its
forged requests are rejected with HTTP 400.

Templates include:  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
"""

import hmac
import logging
import secrets

from flask import abort, request, session

_log = logging.getLogger("security")
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def generate_csrf_token() -> str:
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def init_csrf(app) -> None:
    app.jinja_env.globals["csrf_token"] = generate_csrf_token

    @app.before_request
    def _verify_csrf_token():
        if request.method in SAFE_METHODS:
            return
        expected = session.get("_csrf_token")
        sent = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        if not expected or not sent or not hmac.compare_digest(expected, sent):
            _log.warning("CSRF check failed: %s %s from %s",
                         request.method, request.path, request.remote_addr)
            abort(400, description="Invalid or missing CSRF token.")
