import hashlib
import secrets

from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()


def hash_password(password):
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    return password_hasher.hash(
        password
    )


def verify_password(
    password,
    password_hash
):
    if not isinstance(password, str):
        return False

    if not isinstance(password_hash, str):
        return False

    try:
        return password_hasher.verify(
            password,
            password_hash
        )

    except Exception:
        return False


def generate_access_token():
    return secrets.token_urlsafe(
        32
    )


def hash_access_token(
    access_token
):
    if not isinstance(access_token, str):
        raise ValueError("Access token must be a string")

    return hashlib.sha256(
        access_token.encode(
            "utf-8"
        )
    ).hexdigest()