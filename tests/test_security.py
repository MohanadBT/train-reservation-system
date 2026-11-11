"""
tests/test_security.py
----------------------
Automated tests for the Phase 2 security layers.
Run from the project root:

    python -m unittest tests.test_security -v

Each test uses a temporary database and a temporary encryption key, so it never
touches real data.
"""

import os
import re
import sqlite3
import tempfile
import unittest

# --- Point the app at temporary files BEFORE importing it -------------------
_tmp = tempfile.mkdtemp()
os.environ["DB_PATH"] = os.path.join(_tmp, "test.db")
os.environ["DATA_KEY_FILE"] = os.path.join(_tmp, "test.key")
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ.pop("DATA_ENCRYPTION_KEY", None)

from app import app                                    # noqa: E402
from security import encryption                        # noqa: E402
from security.login_guard import LoginGuard, guard     # noqa: E402
from security.validation import (                      # noqa: E402
    parse_int, parse_price, validate_password_strength)

app.config["TESTING"] = True


def get_token(client, url="/login"):
    """Loads a page and pulls the CSRF token out of the HTML form."""
    html = client.get(url).get_data(as_text=True)
    match = re.search(r'name="csrf_token" value="([0-9a-f]+)"', html)
    return match.group(1) if match else None


def login(client, username, password, role):
    return client.post("/login", data={
        "username": username, "password": password, "role": role,
        "csrf_token": get_token(client)})


class EncryptionTests(unittest.TestCase):
    def test_roundtrip(self):
        enc = encryption.encrypt_value("1234567890")
        self.assertTrue(enc.startswith("enc:v1:"))
        self.assertNotIn("1234567890", enc)
        self.assertEqual(encryption.decrypt_value(enc), "1234567890")

    def test_empty_and_none_pass_through(self):
        self.assertIsNone(encryption.encrypt_value(None))
        self.assertEqual(encryption.encrypt_value(""), "")

    def test_no_double_encryption(self):
        once = encryption.encrypt_value("ABC123")
        self.assertEqual(encryption.encrypt_value(once), once)

    def test_legacy_plaintext_still_readable(self):
        self.assertEqual(encryption.decrypt_value("old-plain-id"), "old-plain-id")

    def test_wrong_key_cannot_decrypt(self):
        enc = encryption.encrypt_value("SECRET-ID")
        os.environ["DATA_ENCRYPTION_KEY"] = encryption.Fernet.generate_key().decode()
        encryption.reset_cache()
        try:
            self.assertEqual(encryption.decrypt_value(enc), "[unreadable]")
        finally:
            del os.environ["DATA_ENCRYPTION_KEY"]
            encryption.reset_cache()

    def test_masking(self):
        self.assertEqual(encryption.mask_value("1234567890"), "******7890")


class DatabaseEncryptionTests(unittest.TestCase):
    """Proves the id_number is unreadable inside the database file itself."""

    def test_id_number_is_encrypted_in_db_but_visible_in_app(self):
        client = app.test_client()
        login(client, "admin", "admin123", "admin")
        token = get_token(client, "/admin/passengers")
        resp = client.post("/admin/passengers/add", data={
            "full_name": "Test Passenger", "id_number": "1098765432",
            "email": "t@example.com", "phone_number": "0500000000",
            "csrf_token": token})
        self.assertEqual(resp.status_code, 302)

        # 1) What an attacker reading the .db file would see
        raw = sqlite3.connect(os.environ["DB_PATH"]).execute(
            "SELECT id_number FROM passengers WHERE full_name='Test Passenger'"
        ).fetchone()[0]
        self.assertTrue(raw.startswith("enc:v1:"))
        self.assertNotIn("1098765432", raw)

        # 2) What an authorised admin sees in the page
        page = client.get("/admin/passengers").get_data(as_text=True)
        self.assertIn("1098765432", page)


class LoginGuardTests(unittest.TestCase):
    def test_locks_after_five_failures_then_unlocks(self):
        now = [1000.0]
        g = LoginGuard(max_attempts=5, window_seconds=900, lockout_seconds=900,
                       clock=lambda: now[0])
        key = g.make_key("admin", "1.2.3.4")
        for _ in range(4):
            self.assertFalse(g.register_failure(key))
        self.assertEqual(g.seconds_locked(key), 0)
        self.assertTrue(g.register_failure(key))        # 5th failure -> lock
        self.assertGreater(g.seconds_locked(key), 0)
        now[0] += 901                                   # wait out the lockout
        self.assertEqual(g.seconds_locked(key), 0)

    def test_other_ip_is_not_locked(self):
        g = LoginGuard(max_attempts=2)
        for _ in range(2):
            g.register_failure(g.make_key("admin", "1.1.1.1"))
        self.assertGreater(g.seconds_locked(g.make_key("admin", "1.1.1.1")), 0)
        self.assertEqual(g.seconds_locked(g.make_key("admin", "2.2.2.2")), 0)

    def test_success_resets_counter(self):
        g = LoginGuard(max_attempts=3)
        key = g.make_key("staff1", "9.9.9.9")
        g.register_failure(key); g.register_failure(key)
        g.reset(key)
        self.assertFalse(g.register_failure(key))

    def test_http_lockout_blocks_even_correct_password(self):
        guard.clear_all()
        client = app.test_client()
        for _ in range(5):
            r = login(client, "staff1", "wrong-password", "staff")
        self.assertEqual(r.status_code, 429)
        r = login(client, "staff1", "staff123", "staff")  # correct, but locked
        self.assertEqual(r.status_code, 429)
        self.assertEqual(client.get("/staff/dashboard").status_code, 302)  # still not logged in
        guard.clear_all()


class CsrfTests(unittest.TestCase):
    def setUp(self):
        guard.clear_all()

    def test_post_without_token_is_rejected(self):
        client = app.test_client()
        self.assertEqual(client.post("/login", data={
            "username": "admin", "password": "admin123", "role": "admin"}).status_code, 400)

    def test_post_with_wrong_token_is_rejected(self):
        client = app.test_client()
        get_token(client)
        self.assertEqual(client.post("/login", data={
            "username": "admin", "password": "admin123", "role": "admin",
            "csrf_token": "0" * 64}).status_code, 400)

    def test_forged_admin_action_is_blocked(self):
        """Simulates a malicious site making a logged-in admin delete a schedule."""
        client = app.test_client()
        login(client, "admin", "admin123", "admin")
        self.assertEqual(client.post("/admin/schedules/delete/1").status_code, 400)

    def test_valid_token_is_accepted(self):
        client = app.test_client()
        self.assertEqual(login(client, "admin", "admin123", "admin").status_code, 302)

    def test_all_post_forms_contain_token(self):
        client = app.test_client()
        login(client, "admin", "admin123", "admin")
        for url in ("/admin/passengers", "/admin/schedules", "/admin/staff",
                    "/admin/reservations", "/staff/dashboard"):
            html = client.get(url).get_data(as_text=True)
            posts = len(re.findall(r'<form method="POST"', html))
            tokens = len(re.findall(r'name="csrf_token"', html))
            self.assertGreaterEqual(tokens, posts, url)


class AccessControlTests(unittest.TestCase):
    """Confirms the existing role checks still hold with the new layers."""

    def setUp(self):
        guard.clear_all()

    def test_anonymous_redirected_from_admin_and_staff(self):
        client = app.test_client()
        self.assertEqual(client.get("/admin/dashboard").status_code, 302)
        self.assertEqual(client.get("/staff/dashboard").status_code, 302)

    def test_staff_cannot_open_admin_pages(self):
        client = app.test_client()
        login(client, "staff1", "staff123", "staff")
        self.assertEqual(client.get("/admin/staff").status_code, 302)
        self.assertEqual(client.get("/admin/passengers").status_code, 302)

    def test_sql_injection_login_fails(self):
        client = app.test_client()
        r = login(client, "admin' OR '1'='1", "x' OR '1'='1", "admin")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(client.get("/admin/dashboard").status_code, 302)  # still not logged in


class HardeningTests(unittest.TestCase):
    def setUp(self):
        guard.clear_all()

    def test_security_headers_present(self):
        h = app.test_client().get("/login").headers
        self.assertEqual(h["X-Content-Type-Options"], "nosniff")
        self.assertEqual(h["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'self'", h["Content-Security-Policy"])

    def test_session_cookie_flags(self):
        client = app.test_client()
        r = login(client, "admin", "admin123", "admin")
        cookie = r.headers.get("Set-Cookie", "")
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)

    def test_logged_in_pages_not_cached(self):
        client = app.test_client()
        login(client, "admin", "admin123", "admin")
        self.assertEqual(client.get("/admin/dashboard").headers["Cache-Control"], "no-store")


class ValidationTests(unittest.TestCase):
    def setUp(self):
        guard.clear_all()

    def test_parsers(self):
        self.assertEqual(parse_int("12"), 12)
        self.assertIsNone(parse_int("abc"))
        self.assertIsNone(parse_int("-5"))
        self.assertEqual(parse_price("45.50"), 45.5)
        self.assertIsNone(parse_price("nan"))

    def test_password_strength(self):
        self.assertFalse(validate_password_strength("abc123")[0])
        self.assertFalse(validate_password_strength("abcdefgh")[0])
        self.assertTrue(validate_password_strength("metro2026")[0])

    def test_bad_schedule_input_no_longer_crashes(self):
        client = app.test_client()
        login(client, "admin", "admin123", "admin")
        token = get_token(client, "/admin/schedules")
        r = client.post("/admin/schedules/add", data={
            "train_id": "1", "route": "A -> B", "departure_time": "2026-01-01T10:00",
            "arrival_time": "2026-01-01T12:00", "ticket_price": "abc",
            "available_seats": "-3", "csrf_token": token})
        self.assertEqual(r.status_code, 302)   # handled with an error message, not HTTP 500

    def test_invalid_role_rejected(self):
        client = app.test_client()
        login(client, "admin", "admin123", "admin")
        token = get_token(client, "/admin/staff")
        client.post("/admin/staff/add", data={
            "username": "hacker", "password": "metro2026", "full_name": "H",
            "role": "superuser", "csrf_token": token})
        users = sqlite3.connect(os.environ["DB_PATH"]).execute(
            "SELECT COUNT(*) FROM users WHERE username='hacker'").fetchone()[0]
        self.assertEqual(users, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
