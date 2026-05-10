# Train Schedule and Reservation Management System

A university Software Engineering project built with Python/Flask + SQLite.
Developed following Agile/Scrum methodology across 3 sprints.

## Tech Stack

- **Backend**: Python 3.11+, Flask
- **Database**: SQLite (via Python's built-in `sqlite3`)
- **Frontend**: HTML/CSS/Jinja2 templates
- **Architecture**: Layered (Presentation → Business Logic → Data Access → Database)

## Project Structure

```
train_system/
├── app.py                        # Main Flask entry point
├── requirements.txt
├── database/
│   ├── db.py                     # DB connection + initialization
│   └── schema.sql                # Table definitions
├── models/
│   └── entities.py               # Data classes (Train, Schedule, Passenger, etc.)
├── repositories/
│   ├── user_repository.py        # DB queries for users
│   ├── schedule_repository.py    # DB queries for trains & schedules
│   ├── passenger_repository.py   # DB queries for passengers
│   └── reservation_repository.py # DB queries for reservations
├── services/
│   ├── auth_service.py           # Authentication business logic
│   └── reservation_service.py    # Reservation business logic + stats
├── routes/
│   ├── auth_routes.py            # /login, /logout
│   ├── admin_routes.py           # /admin/*
│   └── staff_routes.py           # /staff/*
└── templates/
    ├── base.html
    ├── login.html
    ├── admin.html
    ├── staff.html
    ├── schedules.html
    ├── passengers.html
    ├── reservations.html
    ├── reports.html
    └── staff_management.html
```

## Setup & Run

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/train-reservation-system.git
cd train-reservation-system

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py

# 5. Open in browser
# http://127.0.0.1:5000
```

## Default Login Credentials

| Role          | Username | Password  |
|---------------|----------|-----------|
| Administrator | admin    | admin123  |
| Staff         | staff1   | staff123  |

> Change these immediately in a real deployment!

## Features

- Role-based authentication (Admin / Staff)
- Train schedule management (add, edit, delete)
- Passenger records management
- Reservation system with automatic seat validation
- Live dashboard statistics
- Revenue and booking reports
- Staff account management (admin only)

## Packaging as Windows .exe

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" --add-data "database;database" app.py
```

The `.exe` will appear in the `dist/` folder.
