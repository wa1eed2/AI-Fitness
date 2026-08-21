import sqlite3
from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.app import (
    create_app
)

from src.database.query_user_database import (
    delete_user
)

from src.database.setup_auth_database import (
    DB_PATH
)


def create_test_client():
    return TestClient(
        create_app()
    )


def unique_email(
    prefix
):
    return f"{prefix}-{uuid4().hex}@example.com"


def register_user(
    client,
    email=None,
    password="StrongPassword123"
):
    if email is None:
        email = unique_email(
            "auth-test"
        )

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password
        }
    )

    if response.status_code != 201:
        raise ValueError(f"FAIL: Test account registration failed: {response.status_code} {response.text}")

    return response.json()


def auth_headers(
    access_token
):
    return {
        "Authorization": f"Bearer {access_token}"
    }


def test_register_account():
    client = create_test_client()

    data = register_user(
        client
    )

    try:
        if data["token_type"] != "bearer":
            raise ValueError("FAIL: Registration returned incorrect token type")

        if not data["access_token"]:
            raise ValueError("FAIL: Registration did not return access token")

        if data["user_id"] <= 0:
            raise ValueError("FAIL: Registration returned invalid user ID")

        print("PASS: API registers authenticated account")

    finally:
        delete_user(
            data["user_id"]
        )


def test_password_is_not_stored_in_plaintext():
    client = create_test_client()

    password = "NeverStoreThis123"

    data = register_user(
        client,
        password=password
    )

    try:
        connection = sqlite3.connect(
            DB_PATH
        )

        row = connection.execute(
            """
            SELECT password_hash
            FROM user_accounts
            WHERE user_id = ?
            """,
            (
                data["user_id"],
            )
        ).fetchone()

        connection.close()

        if row is None:
            raise ValueError("FAIL: Password hash was not stored")

        if row[0] == password:
            raise ValueError("FAIL: Password was stored in plaintext")

        if password in row[0]:
            raise ValueError("FAIL: Stored password hash contains plaintext password")

        print("PASS: Password is stored only as a secure hash")

    finally:
        delete_user(
            data["user_id"]
        )


def test_email_normalization_prevents_duplicates():
    client = create_test_client()

    email = unique_email(
        "duplicate"
    )

    first = register_user(
        client,
        email=email.lower()
    )

    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email.upper(),
                "password": "AnotherPassword123"
            }
        )

        if response.status_code != 409:
            raise ValueError(f"FAIL: Duplicate normalized email returned HTTP {response.status_code}")

        print("PASS: API prevents case-insensitive duplicate email")

    finally:
        delete_user(
            first["user_id"]
        )


def test_invalid_email_rejected():
    client = create_test_client()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword123"
        }
    )

    if response.status_code != 422:
        raise ValueError("FAIL: Invalid registration email did not return HTTP 422")

    print("PASS: API rejects invalid registration email")


def test_short_password_rejected():
    client = create_test_client()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email(
                "short-password"
            ),
            "password": "short"
        }
    )

    if response.status_code != 422:
        raise ValueError("FAIL: Short registration password did not return HTTP 422")

    print("PASS: API rejects short registration password")


def test_login_returns_access_token():
    client = create_test_client()

    email = unique_email(
        "login"
    )

    password = "LoginPassword123"

    registered = register_user(
        client,
        email=email,
        password=password
    )

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Login returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if not data["access_token"]:
            raise ValueError("FAIL: Login did not return access token")

        if data["user_id"] != registered["user_id"]:
            raise ValueError("FAIL: Login returned incorrect user")

        print("PASS: API login returns access token")

    finally:
        delete_user(
            registered["user_id"]
        )


def test_wrong_password_rejected():
    client = create_test_client()

    email = unique_email(
        "wrong-password"
    )

    registered = register_user(
        client,
        email=email,
        password="CorrectPassword123"
    )

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "WrongPassword123"
            }
        )

        if response.status_code != 401:
            raise ValueError("FAIL: Wrong password did not return HTTP 401")

        print("PASS: API rejects incorrect password")

    finally:
        delete_user(
            registered["user_id"]
        )


def test_unknown_email_rejected():
    client = create_test_client()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": unique_email(
                "missing-account"
            ),
            "password": "SomePassword123"
        }
    )

    if response.status_code != 401:
        raise ValueError("FAIL: Unknown login email did not return HTTP 401")

    if response.json()["detail"] != "Invalid email or password":
        raise ValueError("FAIL: Unknown email exposed a different login error")

    print("PASS: API uses generic invalid-login response")


def test_authenticated_me_endpoint():
    client = create_test_client()

    registered = register_user(
        client
    )

    try:
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers(
                registered["access_token"]
            )
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Authenticated /me returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["user_id"] != registered["user_id"]:
            raise ValueError("FAIL: /me returned incorrect user")

        if data["email"] != registered["email"]:
            raise ValueError("FAIL: /me returned incorrect email")

        if data["is_active"] is not True:
            raise ValueError("FAIL: /me returned inactive account")

        print("PASS: API returns authenticated current user")

    finally:
        delete_user(
            registered["user_id"]
        )


def test_me_requires_authentication():
    client = create_test_client()

    response = client.get(
        "/api/v1/auth/me"
    )

    if response.status_code != 401:
        raise ValueError("FAIL: Unauthenticated /me did not return HTTP 401")

    print("PASS: Current-user endpoint requires authentication")


def test_invalid_access_token_rejected():
    client = create_test_client()

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(
            "invalid-token"
        )
    )

    if response.status_code != 401:
        raise ValueError("FAIL: Invalid bearer token did not return HTTP 401")

    print("PASS: API rejects invalid access token")


def test_logout_revokes_access_token():
    client = create_test_client()

    registered = register_user(
        client
    )

    try:
        token = registered[
            "access_token"
        ]

        response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers(
                token
            )
        )

        if response.status_code != 204:
            raise ValueError("FAIL: Logout did not return HTTP 204")

        me_response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers(
                token
            )
        )

        if me_response.status_code != 401:
            raise ValueError("FAIL: Logged-out access token remained valid")

        print("PASS: Logout revokes access token")

    finally:
        delete_user(
            registered["user_id"]
        )


def test_tokens_are_isolated_by_account():
    client = create_test_client()

    first = register_user(
        client
    )

    second = register_user(
        client
    )

    try:
        first_me = client.get(
            "/api/v1/auth/me",
            headers=auth_headers(
                first["access_token"]
            )
        ).json()

        second_me = client.get(
            "/api/v1/auth/me",
            headers=auth_headers(
                second["access_token"]
            )
        ).json()

        if first_me["user_id"] != first["user_id"]:
            raise ValueError("FAIL: First token returned incorrect user")

        if second_me["user_id"] != second["user_id"]:
            raise ValueError("FAIL: Second token returned incorrect user")

        if first_me["user_id"] == second_me["user_id"]:
            raise ValueError("FAIL: Authentication tokens were not isolated")

        print("PASS: Access tokens are isolated by account")

    finally:
        delete_user(
            first["user_id"]
        )

        delete_user(
            second["user_id"]
        )


def test_deleting_user_cascades_auth_data():
    client = create_test_client()

    registered = register_user(
        client
    )

    user_id = registered[
        "user_id"
    ]

    access_token = registered[
        "access_token"
    ]

    delete_user(
        user_id
    )

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(
            access_token
        )
    )

    if response.status_code != 401:
        raise ValueError("FAIL: Deleted user's authentication session remained valid")

    connection = sqlite3.connect(
        DB_PATH
    )

    account_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM user_accounts
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    ).fetchone()[0]

    session_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM auth_sessions
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    ).fetchone()[0]

    connection.close()

    if account_count != 0:
        raise ValueError("FAIL: User account did not cascade on user deletion")

    if session_count != 0:
        raise ValueError("FAIL: Auth sessions did not cascade on user deletion")

    print("PASS: User deletion cascades authentication data")


def test_auth_routes_appear_in_openapi():
    client = create_test_client()

    response = client.get(
        "/openapi.json"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: OpenAPI schema was unavailable")

    paths = response.json()[
        "paths"
    ]

    expected_paths = {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/me",
        "/api/v1/auth/logout"
    }

    if not expected_paths.issubset(
        set(
            paths.keys()
        )
    ):
        raise ValueError("FAIL: OpenAPI schema is missing authentication routes")

    print("PASS: OpenAPI documentation includes authentication routes")


if __name__ == "__main__":
    test_register_account()
    test_password_is_not_stored_in_plaintext()
    test_email_normalization_prevents_duplicates()
    test_invalid_email_rejected()
    test_short_password_rejected()
    test_login_returns_access_token()
    test_wrong_password_rejected()
    test_unknown_email_rejected()
    test_authenticated_me_endpoint()
    test_me_requires_authentication()
    test_invalid_access_token_rejected()
    test_logout_revokes_access_token()
    test_tokens_are_isolated_by_account()
    test_deleting_user_cascades_auth_data()
    test_auth_routes_appear_in_openapi()