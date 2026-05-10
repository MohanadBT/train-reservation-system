"""
services/reservation_service.py
---------------------------------
Business Logic Layer - handles reservation rules.
Validates seat availability before confirming.
Coordinates between repositories.
"""

from repositories import reservation_repository, schedule_repository, passenger_repository


def create_reservation(passenger_id: int, schedule_id: int, seat_class: str, created_by: int) -> tuple[bool, str, int | None]:
    """
    Creates a reservation after validating all business rules.
    Returns (success, message, reservation_id).
    """
    # 1. Check schedule exists and is active
    schedule = schedule_repository.find_by_id(schedule_id)
    if not schedule:
        return False, "Schedule not found.", None
    if schedule.status != "active":
        return False, "This schedule is no longer active.", None

    # 2. Validate seat availability
    if schedule.available_seats <= 0:
        return False, "No seats available on this schedule.", None

    # 3. Check passenger exists
    passenger = passenger_repository.find_by_id(passenger_id)
    if not passenger:
        return False, "Passenger not found.", None

    # 4. Create reservation in DB
    reservation_id = reservation_repository.create(passenger_id, schedule_id, seat_class, created_by)

    # 5. Decrement available seats
    schedule_repository.decrement_seat(schedule_id)

    return True, "Reservation confirmed successfully.", reservation_id


def cancel_reservation(reservation_id: int) -> tuple[bool, str]:
    """
    Cancels a reservation and restores the seat.
    """
    reservation = reservation_repository.find_by_id(reservation_id)
    if not reservation:
        return False, "Reservation not found."
    if reservation.status == "cancelled":
        return False, "Reservation is already cancelled."

    reservation_repository.cancel(reservation_id)
    schedule_repository.increment_seat(reservation.schedule_id)

    return True, "Reservation cancelled and seat restored."


def get_dashboard_stats_staff() -> dict:
    """Returns stats shown on staff dashboard."""
    return {
        "bookings_today": reservation_repository.count_today(),
        "cancellations_today": reservation_repository.count_cancellations_today(),
        "available_seats_total": _total_available_seats(),
    }


def get_dashboard_stats_admin() -> dict:
    """Returns stats shown on admin dashboard."""
    from repositories import schedule_repository as sr
    schedules = sr.get_all_schedules()
    total_trains = len(set(s.train_id for s in schedules))
    total_bookings = len(reservation_repository.get_all())
    revenue = reservation_repository.total_revenue()

    total_capacity = sum(s.available_seats for s in schedules)
    total_seats_all = sum(1 for _ in schedules)  # rough

    occupancy = 0
    if schedules:
        from repositories.schedule_repository import get_all_trains
        trains = get_all_trains()
        total_max = sum(t.total_seats for t in trains)
        total_avail = sum(s.available_seats for s in schedules if s.status == "active")
        if total_max > 0:
            occupancy = round(((total_max - total_avail) / total_max) * 100)

    return {
        "total_trains": len(set(s.train_id for s in schedules)),
        "total_bookings": total_bookings,
        "occupancy_rate": f"{occupancy}%",
        "monthly_revenue": f"${revenue:,.0f}",
    }


def _total_available_seats() -> int:
    schedules = schedule_repository.get_active_schedules()
    return sum(s.available_seats for s in schedules)
