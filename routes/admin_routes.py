"""
routes/admin_routes.py
-----------------------
Presentation Layer - all admin-only pages.
Every route here requires role == 'admin'.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from services import reservation_service, auth_service
from repositories import schedule_repository, passenger_repository, user_repository

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ── Access control decorator ──────────────────────────────────────────────────

def admin_required(f):
    """Redirect to login if not an admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in.", "error")
            return redirect(url_for("auth.login_page"))
        if session.get("role") != "admin":
            flash("Administrator access required.", "error")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    stats = reservation_service.get_dashboard_stats_admin()
    schedules = schedule_repository.get_active_schedules()[:10]  # latest 10
    return render_template("admin.html", stats=stats, schedules=schedules,
                           full_name=session.get("full_name"))


# ── Train Schedules ───────────────────────────────────────────────────────────

@admin_bp.route("/schedules")
@admin_required
def schedules():
    all_schedules = schedule_repository.get_all_schedules()
    trains = schedule_repository.get_all_trains()
    return render_template("schedules.html", schedules=all_schedules, trains=trains,
                           full_name=session.get("full_name"))


@admin_bp.route("/schedules/add", methods=["POST"])
@admin_required
def add_schedule():
    train_id = request.form.get("train_id")
    route = request.form.get("route", "").strip()
    departure = request.form.get("departure_time")
    arrival = request.form.get("arrival_time")
    price = request.form.get("ticket_price", 0)
    seats = request.form.get("available_seats", 0)

    if not all([train_id, route, departure, arrival]):
        flash("All fields are required.", "error")
    else:
        schedule_repository.create_schedule(train_id, route, departure, arrival, float(price), int(seats))
        flash("Schedule added successfully.", "success")

    return redirect(url_for("admin.schedules"))


@admin_bp.route("/schedules/delete/<int:schedule_id>", methods=["POST"])
@admin_required
def delete_schedule(schedule_id):
    schedule_repository.delete_schedule(schedule_id)
    flash("Schedule deleted.", "success")
    return redirect(url_for("admin.schedules"))


@admin_bp.route("/schedules/edit/<int:schedule_id>", methods=["POST"])
@admin_required
def edit_schedule(schedule_id):
    route = request.form.get("route", "").strip()
    departure = request.form.get("departure_time")
    arrival = request.form.get("arrival_time")
    price = request.form.get("ticket_price", 0)
    seats = request.form.get("available_seats", 0)
    status = request.form.get("status", "active")

    schedule_repository.update_schedule(schedule_id, route, departure, arrival, float(price), int(seats), status)
    flash("Schedule updated.", "success")
    return redirect(url_for("admin.schedules"))


# ── Passenger Records ─────────────────────────────────────────────────────────

@admin_bp.route("/passengers")
@admin_required
def passengers():
    query = request.args.get("q", "")
    if query:
        passenger_list = passenger_repository.search(query)
    else:
        passenger_list = passenger_repository.get_all()
    return render_template("passengers.html", passengers=passenger_list, query=query,
                           full_name=session.get("full_name"))


@admin_bp.route("/passengers/add", methods=["POST"])
@admin_required
def add_passenger():
    full_name = request.form.get("full_name", "").strip()
    id_number = request.form.get("id_number", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone_number", "").strip()

    if not full_name:
        flash("Passenger name is required.", "error")
    else:
        passenger_repository.create(full_name, id_number, email, phone)
        flash("Passenger added.", "success")

    return redirect(url_for("admin.passengers"))


@admin_bp.route("/passengers/delete/<int:passenger_id>", methods=["POST"])
@admin_required
def delete_passenger(passenger_id):
    passenger_repository.delete(passenger_id)
    flash("Passenger deleted.", "success")
    return redirect(url_for("admin.passengers"))


# ── Reservations ──────────────────────────────────────────────────────────────

@admin_bp.route("/reservations")
@admin_required
def reservations():
    from repositories import reservation_repository
    all_res = reservation_repository.get_all()
    return render_template("reservations.html", reservations=all_res,
                           full_name=session.get("full_name"))


# ── Reports ───────────────────────────────────────────────────────────────────

@admin_bp.route("/reports")
@admin_required
def reports():
    from repositories import reservation_repository
    stats = reservation_service.get_dashboard_stats_admin()
    all_res = reservation_repository.get_all()
    revenue = reservation_repository.total_revenue()
    return render_template("reports.html", stats=stats, reservations=all_res,
                           revenue=revenue, full_name=session.get("full_name"))


# ── Staff Management ──────────────────────────────────────────────────────────

@admin_bp.route("/staff")
@admin_required
def staff_management():
    users = user_repository.get_all()
    return render_template("staff_management.html", users=users,
                           full_name=session.get("full_name"))


@admin_bp.route("/staff/add", methods=["POST"])
@admin_required
def add_staff():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone_number", "").strip()
    role = request.form.get("role", "staff")

    success, msg = auth_service.create_staff_account(username, password, full_name, email, phone, role)
    flash(msg, "success" if success else "error")
    return redirect(url_for("admin.staff_management"))
