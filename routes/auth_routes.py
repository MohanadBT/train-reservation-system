"""
routes/auth_routes.py
----------------------
Presentation Layer - handles login/logout HTTP requests.
Calls auth_service, manages Flask session.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services import auth_service
from security.login_guard import guard

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET"])
@auth_bp.route("/login", methods=["GET"])
def login_page():
    """Show the login page. Redirect if already logged in."""
    if "user_id" in session:
        return _redirect_by_role(session.get("role"))
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login_submit():
    """Process login form submission."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "")

    if role not in ("admin", "staff"):
        flash("Please select a valid role.", "error")
        return redirect(url_for("auth.login_page"))

    # SECURITY: brute-force protection - refuse while this username+IP is locked
    key = guard.make_key(username, request.remote_addr)
    wait = guard.seconds_locked(key)
    if wait:
        flash(f"Too many failed attempts. Try again in {wait // 60 + 1} minute(s).", "error")
        return render_template("login.html"), 429

    success, error_msg, user = auth_service.login(username, password, role)

    if not success:
        if guard.register_failure(key):
            flash("Too many failed attempts. This account is locked for 15 minutes.", "error")
            return render_template("login.html"), 429
        flash(error_msg, "error")
        return redirect(url_for("auth.login_page"))

    guard.reset(key)

    # SECURITY: start a fresh session on login (prevents session fixation)
    session.clear()
    session.permanent = True   # expires after 30 min (see security/hardening.py)
    session["user_id"] = user.id
    session["username"] = user.username
    session["full_name"] = user.full_name
    session["role"] = user.role

    return _redirect_by_role(user.role)


@auth_bp.route("/logout")
def logout():
    """Clear session and redirect to login."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login_page"))


def _redirect_by_role(role: str):
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("staff.dashboard"))
