import sqlite3
from datetime import datetime, timedelta, timezone

from src.auth.security import (
    generate_access_token,
    hash_access_token
)

from src.database.setup_auth_database import (
    get_connection
)


DEFAULT_ACCESS_TOKEN_HOURS = 24


def normalize_email(
    email
):
    if not isinstance(email, str):
        raise ValueError("Email must be a string")

    normalized = email.strip().lower()

    if not normalized:
        raise ValueError("Email cannot be empty")

    return normalized


def create_account(
    email,
    password_hash
):
    normalized_email = normalize_email(
        email
    )

    if not isinstance(password_hash, str):
        raise ValueError("Password hash must be a string")

    if not password_hash:
        raise ValueError("Password hash cannot be empty")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users DEFAULT VALUES
            """
        )

        user_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO user_accounts (
                user_id,
                email,
                normalized_email,
                password_hash
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                email.strip(),
                normalized_email,
                password_hash
            )
        )

        account_id = cursor.lastrowid

        connection.commit()

        return {
            "account_id": account_id,
            "user_id": user_id
        }

    except sqlite3.IntegrityError:
        connection.rollback()
        raise

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_account_by_email(
    email
):
    normalized_email = normalize_email(
        email
    )

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                account_id,
                user_id,
                email,
                normalized_email,
                password_hash,
                is_active,
                created_at,
                updated_at
            FROM user_accounts
            WHERE normalized_email = ?
            """,
            (
                normalized_email,
            )
        ).fetchone()

        if row is None:
            return None

        return dict(
            row
        )

    finally:
        connection.close()


def get_account_by_user_id(
    user_id
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                account_id,
                user_id,
                email,
                normalized_email,
                password_hash,
                is_active,
                created_at,
                updated_at
            FROM user_accounts
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        ).fetchone()

        if row is None:
            return None

        return dict(
            row
        )

    finally:
        connection.close()


def create_auth_session(
    user_id,
    expires_in_hours=DEFAULT_ACCESS_TOKEN_HOURS
):
    if not isinstance(expires_in_hours, int) or isinstance(expires_in_hours, bool) or expires_in_hours <= 0:
        raise ValueError("Token lifetime must be a positive integer")

    access_token = generate_access_token()

    token_hash = hash_access_token(
        access_token
    )

    now = datetime.now(
        timezone.utc
    )

    expires_at = now + timedelta(
        hours=expires_in_hours
    )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO auth_sessions (
                user_id,
                token_hash,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                token_hash,
                now.isoformat(),
                expires_at.isoformat()
            )
        )

        session_id = cursor.lastrowid

        connection.commit()

        return {
            "session_id": session_id,
            "user_id": user_id,
            "access_token": access_token,
            "expires_at": expires_at.isoformat()
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_active_session_by_token(
    access_token
):
    token_hash = hash_access_token(
        access_token
    )

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                session_id,
                user_id,
                token_hash,
                created_at,
                expires_at,
                revoked_at
            FROM auth_sessions
            WHERE token_hash = ?
            """,
            (
                token_hash,
            )
        ).fetchone()

        if row is None:
            return None

        session = dict(
            row
        )

        if session["revoked_at"] is not None:
            return None

        expires_at = datetime.fromisoformat(
            session["expires_at"]
        )

        if expires_at <= datetime.now(
            timezone.utc
        ):
            return None

        return session

    finally:
        connection.close()


def get_active_auth_sessions(
    user_id
):
    now = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                session_id,
                user_id,
                created_at,
                expires_at
            FROM auth_sessions
            WHERE user_id = ?
              AND revoked_at IS NULL
              AND expires_at > ?
            ORDER BY created_at DESC
            """,
            (
                user_id,
                now
            )
        ).fetchall()

        return [
            dict(
                row
            )
            for row in rows
        ]

    finally:
        connection.close()


def revoke_auth_session(
    access_token
):
    token_hash = hash_access_token(
        access_token
    )

    revoked_at = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE auth_sessions
            SET revoked_at = ?
            WHERE token_hash = ?
              AND revoked_at IS NULL
            """,
            (
                revoked_at,
                token_hash
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def revoke_all_auth_sessions(
    user_id
):
    revoked_at = datetime.now(
        timezone.utc
    ).isoformat()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE auth_sessions
            SET revoked_at = ?
            WHERE user_id = ?
              AND revoked_at IS NULL
            """,
            (
                revoked_at,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()