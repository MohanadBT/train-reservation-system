"""
models/entities.py
------------------
Model Layer - defines the data classes (entities) used across the system.
These mirror the class diagram from Sprint 2.
Attributes are private-style (_name); public methods expose them.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Represents a StaffMember or Administrator (role field differentiates)."""
    id: Optional[int]
    username: str
    password_hash: str
    full_name: str
    email: Optional[str]
    phone_number: Optional[str]
    role: str          # 'admin' or 'staff'
    created_at: Optional[str] = None

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_staff(self) -> bool:
        return self.role in ("admin", "staff")  # admins can do staff actions too


@dataclass
class Train:
    id: Optional[int]
    train_number: str    # e.g. TR-110
    name: Optional[str]
    total_seats: int


@dataclass
class Schedule:
    id: Optional[int]
    train_id: int
    route: str
    departure_time: str
    arrival_time: str
    ticket_price: float
    available_seats: int
    status: str = "active"
    train_number: Optional[str] = None  # joined from trains table for display


@dataclass
class Passenger:
    id: Optional[int]
    full_name: str
    id_number: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    created_at: Optional[str] = None


@dataclass
class Reservation:
    id: Optional[int]
    passenger_id: int
    schedule_id: int
    seat_class: str
    status: str
    booking_reference: str
    created_by: int
    created_at: Optional[str] = None
    # Display fields (joined from other tables)
    passenger_name: Optional[str] = None
    train_number: Optional[str] = None
    route: Optional[str] = None
