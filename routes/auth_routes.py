"""
routes/auth_routes.py
----------------------
Presentation Layer - handles login/logout HTTP requests.
Calls auth_service, manages Flask session.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services import auth_service

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

    success, error_msg, user = auth_service.login(username, password, role)

    if not success:
        flash(error_msg, "error")
        return redirect(url_for("auth.login_page"))

    # Store user info in session
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
