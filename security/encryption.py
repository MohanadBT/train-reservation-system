"""
security/encryption.py
----------------------
Field-level ("record") encryption for sensitive data stored in the database.

Why: passengers.id_number holds a national ID / passport number. Before this
module it was stored as plain text in the SQLite file, so anyone who could read
the .db file could read every passenger's identity number.

How: values are encrypted with Fernet (AES-128-CBC + HMAC-SHA256, from the
`cryptography` library) before being written, and decrypted when read.
Encrypted values are stored as  "enc:v1:<token>"  so the code can tell them
apart from old plain-text rows (backward compatible).

Key management:
    1. DATA_ENCRYPTION_KEY environment variable (recommended for deployment), or
    2. instance/data.key  - generated automatically on first run (git-ignored).
Losing the key means losing the encrypted data, so back it up separately
from the database.
"""

import logging
import os
import threading

from cryptography.fernet import Fernet, InvalidToken

PREFIX = "enc:v1:"

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_KEY_FILE = os.path.join(_BASE_DIR, "instance", "data.key")

_log = logging.getLogger("security")
_lock = threading.Lock()
_fernet = None


def _load_key() -> bytes:
    """Returns the encryption key, creating a key file on first run."""
    env_key = os.environ.get("DATA_ENCRYPTION_KEY")
    if env_key:
        return env_key.encode()

    key_file = os.environ.get("DATA_KEY_FILE", _DEFAULT_KEY_FILE)
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read().strip()

    os.makedirs(os.path.dirname(key_file), exist_ok=True)
    key = Fernet.generate_key()
    with open(key_file, "wb") as f:
        f.write(key)
    try:
        os.chmod(key_file, 0o600)  # owner read/write only (no effect on Windows)
    except OSError:
        pass
    _log.warning("New encryption key created at %s - back it up!", key_file)
    return key


def _get_fernet() -> Fernet:
    global _fernet
    with _lock:
        if _fernet is None:
            _fernet = Fernet(_load_key())
        return _fernet


def reset_cache() -> None:
    """Forget the loaded key (used by tests that switch keys)."""
    global _fernet
    with _lock:
        _fernet = None


def is_encrypted(value) -> bool:
    return isinstance(value, str) and value.startswith(PREFIX)


def encrypt_value(value):
    """Encrypts a string. None / empty / already-encrypted values pass through."""
    if value is None or value == "" or is_encrypted(value):
        return value
    token = _get_fernet().encrypt(value.encode("utf-8")).decode("ascii")
    return PREFIX + token


def decrypt_value(value):
    """
    Decrypts a stored value.
    Old plain-text rows (no prefix) are returned unchanged so the system keeps
    working until scripts/encrypt_existing_data.py has been run.
    """
    if not is_encrypted(value):
        return value
    try:
        return _get_fernet().decrypt(value[len(PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken:
        _log.error("Could not decrypt a stored value (wrong key or corrupted data).")
        return "[unreadable]"


def mask_value(value, visible: int = 4) -> str:
    """Shows only the last few characters, e.g. '******7890' (for display/logs)."""
    if not value:
        return ""
    if len(value) <= visible:
        return "*" * len(value)
    return "*" * (len(value) - visible) + value[-visible:]
