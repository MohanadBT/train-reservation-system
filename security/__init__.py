"""
security package
----------------
Extra protection layers added in Phase 2 (Security Implementation):

    encryption.py   - field-level encryption of sensitive passenger data (Fernet / AES)
    login_guard.py  - temporary lockout after repeated failed logins (anti brute-force)
    csrf.py         - CSRF token protection for every state-changing request
    hardening.py    - secure session cookies + HTTP security headers
    validation.py   - input validation (numbers, roles, password strength)
"""
