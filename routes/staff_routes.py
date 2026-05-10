"""
routes/staff_routes.py
-----------------------
Presentation Layer - staff dashboard and reservation management.
Accessible by both 'staff' and 'admin' roles.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from services import reservation_service
from repositories import schedule_repository, passenger_repository, reservation_repository

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


# ── Access control ─────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in.", "error")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ─────────────────────────────────────────────────────────────────

@staff_bp.route("/dashboard")
@login_required
def dashboard():
    stats = reservation_service.get_dashboard_stats_staff()
    schedules = schedule_repository.get_active_schedules()
    passengers = passenger_repository.get_all()
    recent_reservations = reservation_repository.get_all()[:20]
    return render_template("staff.html",
                           stats=stats,
                           schedules=schedules,
                           passengers=passengers,
                           recent_reservations=recent_reservations,
                           full_name=session.get("full_name"),
                           role=session.get("role"))


# ── Reservations ──────────────────────────────────────────────────────────────

@staff_bp.route("/reserve", methods=["POST"])
@login_required
def make_reservation():
    passenger_id = request.form.get("passenger_id")
    schedule_id = request.form.get("schedule_id")
    seat_class = request.form.get("seat_class", "Economy")
    user_id = session.get("user_id")

    if not passenger_id or not schedule_id:
        flash("Please select a passenger and a schedule.", "error")
        return redirect(url_for("staff.dashboard"))

    success, msg, res_id = reservation_service.create_reservation(
        int(passenger_id), int(schedule_id), seat_class, user_id
    )
    flash(msg, "success" if success else "error")
    return redirect(url_for("staff.dashboard"))


@staff_bp.route("/cancel/<int:reservation_id>", methods=["POST"])
@login_required
def cancel_reservation(reservation_id):
    success, msg = reservation_service.cancel_reservation(reservation_id)
    flash(msg, "success" if success else "error")
    return redirect(url_for("staff.dashboard"))
