"""
security/login_guard.py
-----------------------
Protection against password guessing (brute force).

Rule: after MAX_ATTEMPTS failed logins for the same username from the same IP
inside WINDOW_SECONDS, that username+IP pair is locked for LOCKOUT_SECONDS.
A successful login clears the counter.

Only FAILED logins are counted, so normal traffic (including the 200-request
reliability test with valid credentials) is not affected.

Limitations (documented on purpose): state is kept in memory, so it resets when
the server restarts, and it is per-process. A production system would keep it
in a shared store such as Redis or the database.
"""

import logging
import threading
import time

_log = logging.getLogger("security")


class LoginGuard:
    def __init__(self, max_attempts=5, window_seconds=15 * 60,
                 lockout_seconds=15 * 60, clock=time.time):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self.lockout = lockout_seconds
        self._clock = clock
        self._failures = {}      # key -> list of failure timestamps
        self._locked_until = {}  # key -> unlock timestamp
        self._lock = threading.Lock()

    @staticmethod
    def make_key(username: str, ip: str) -> str:
        return f"{(username or '').strip().lower()}|{ip or 'unknown'}"

    def seconds_locked(self, key: str) -> int:
        """Seconds left on the lockout, or 0 if the key is not locked."""
        with self._lock:
            until = self._locked_until.get(key)
            if until is None:
                return 0
            remaining = until - self._clock()
            if remaining <= 0:
                del self._locked_until[key]
                self._failures.pop(key, None)
                return 0
            return int(remaining) + 1

    def register_failure(self, key: str) -> bool:
        """Records a failed attempt. Returns True if this attempt caused a lockout."""
        now = self._clock()
        with self._lock:
            recent = [t for t in self._failures.get(key, []) if now - t < self.window]
            recent.append(now)
            self._failures[key] = recent
            if len(recent) >= self.max_attempts:
                self._locked_until[key] = now + self.lockout
                _log.warning("LOCKOUT: %s locked for %ss after %s failed logins",
                             key, self.lockout, len(recent))
                return True
            return False

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)
            self._locked_until.pop(key, None)

    def clear_all(self) -> None:
        with self._lock:
            self._failures.clear()
            self._locked_until.clear()


# One shared guard for the whole app
guard = LoginGuard()
