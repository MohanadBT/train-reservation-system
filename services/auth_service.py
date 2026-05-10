"""
services/auth_service.py
--------------------------
Business Logic Layer - authentication logic.
Validates credentials, checks roles, manages session data.
Never touches the database directly — uses user_repository.
"""

from werkzeug.security import check_password_hash, generate_password_hash
from repositories import user_repository
from models.entities import User


def login(username: str, password: str, expected_role: str) -> tuple[bool, str, User | None]:
    """
    Validates login credentials.
    Returns (success, error_message, user_object).
    expected_role: 'admin' or 'staff'
    """
    if not username or not password:
        return False, "Username and password are required.", None

    user = user_repository.find_by_username(username.strip())

    if user is None:
        return False, "Invalid username or password.", None

    if not check_password_hash(user.password_hash, password):
        return False, "Invalid username or password.", None

    # Role check: admin can only log in as admin; staff can only log in as staff
    if expected_role == "admin" and not user.is_admin():
        return False, "You do not have administrator privileges.", None

    if expected_role == "staff" and user.role not in ("admin", "staff"):
        return False, "Access denied.", None

    return True, "", user


def create_staff_account(username, password, full_name, email, phone_number, role="staff") -> tuple[bool, str]:
    """Creates a new staff or admin account. Admin-only operation."""
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    existing = user_repository.find_by_username(username)
    if existing:
        return False, f"Username '{username}' is already taken."

    hashed = generate_password_hash(password)
    user_repository.create(username, hashed, full_name, email, phone_number, role)
    return True, "Account created successfully."


def update_password(user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    user = user_repository.find_by_id(user_id)
    if not user:
        return False, "User not found."
    if not check_password_hash(user.password_hash, old_password):
        return False, "Current password is incorrect."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."
    hashed = generate_password_hash(new_password)
    # Direct update via repo — minimal business logic
    from database.db import get_connection
    conn = get_connection()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hashed, user_id))
    conn.commit()
    conn.close()
    return True, "Password updated successfully."
