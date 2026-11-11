"""
scripts/encrypt_existing_data.py
--------------------------------
One-time migration: encrypts passengers.id_number values that are still stored
as plain text. Safe to run more than once (already-encrypted rows are skipped).

Run from the project root:
    python -m scripts.encrypt_existing_data
"""

from database.db import get_connection
from security.encryption import encrypt_value, is_encrypted


def main():
    conn = get_connection()
    rows = conn.execute("SELECT id, id_number FROM passengers").fetchall()
    changed = 0
    for row in rows:
        value = row["id_number"]
        if value and not is_encrypted(value):
            conn.execute("UPDATE passengers SET id_number=? WHERE id=?",
                         (encrypt_value(value), row["id"]))
            changed += 1
    conn.commit()
    conn.close()
    print(f"Done. {changed} of {len(rows)} passenger rows encrypted.")


if __name__ == "__main__":
    main()
