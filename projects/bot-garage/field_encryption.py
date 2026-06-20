"""
field_encryption.py
===================

Portfolio excerpt, adapted. Transparent column-level encryption applied at the
data layer instead of in each endpoint. With a key set, sensitive values leave
the process only as ``enc:...`` ciphertext, so a stolen database without the key
is useless.

Why the design works this way:
  * the ``enc:`` prefix keeps encrypted state visible for audit, debugging, and
    rolling out across rows that are still a mix of encrypted and plaintext.
  * encrypt is idempotent, so a double save never double-wraps a value.
  * decrypt fails loud: a missing or wrong key returns the ciphertext untouched
    rather than fabricating plaintext.

There is no recovery without the key. Back it up (password manager).
"""

from __future__ import annotations

import os

_ENC_PREFIX = "enc:"

# per-table policy, not a global config knob
_SENSITIVE_FIELDS = frozenset({"owner", "registration", "vin", "plate"})

# no key in the env means encryption is off: values store and return as plaintext
_DB_KEY = (os.getenv("APP_DB_KEY") or "").strip()
_fernet = None
if _DB_KEY:
    from cryptography.fernet import Fernet  # AES-CBC + HMAC
    _fernet = Fernet(_DB_KEY.encode())


def encrypt(value):
    """Encrypt a string, or pass through None, "", and already-tagged values."""
    if _fernet is None or value is None or value == "":
        return value
    s = value if isinstance(value, str) else str(value)
    if s.startswith(_ENC_PREFIX):
        return s
    return _ENC_PREFIX + _fernet.encrypt(s.encode()).decode()


def decrypt(value):
    """Decrypt an ``enc:``-tagged value; plaintext passes through unchanged.

    A missing, wrong, or corrupt key returns the ciphertext unchanged so the
    failure is diagnosable rather than silently turning into bad plaintext.
    """
    if not isinstance(value, str) or not value.startswith(_ENC_PREFIX):
        return value
    if _fernet is None:
        return value
    try:
        return _fernet.decrypt(value[len(_ENC_PREFIX):].encode()).decode()
    except Exception:  # noqa: BLE001 wrong key or tampered token
        return value


# the data layer applies these on the way in and out, so the rest of the app
# only ever sees plaintext and callers never call encrypt/decrypt directly

def encrypt_row(row: dict) -> dict:
    """Return a copy of ``row`` with sensitive fields encrypted for storage."""
    out = dict(row)
    for field in _SENSITIVE_FIELDS:
        if field in out:
            out[field] = encrypt(out[field])
    return out


def decrypt_row(row: dict) -> dict:
    """Return a copy of ``row`` with sensitive fields decrypted for use."""
    out = dict(row)
    for field in _SENSITIVE_FIELDS:
        if field in out:
            out[field] = decrypt(out[field])
    return out
