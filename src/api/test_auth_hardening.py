from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)


def test_legacy_user_creation_removed():
    client = create_test_client()

    response = client.post(
        "/api/v1/users"
    )

    if response.status_code != 404:
        raise ValueError(f"FAIL: Legacy POST /users returned HTTP {response.status_code} instead of 404")

    print("PASS: Legacy unauthenticated user creation is removed")


def test_registered_user_has_active_session():
    client = create_test_client()

    account = register_account(
        client,
        "session-list"
    )

    try:
        response = client.get(
            "/api/v1/auth/sessions",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Session listing returned HTTP {response.status_code}: {response.text}")

        sessions = response.json()

        if len(sessions) != 1:
            raise ValueError("FAIL: Registration did not create exactly one active session")

        if sessions[0]["user_id"] != account["user_id"]:
            raise ValueError("FAIL: Active session belongs to incorrect user")

        print("PASS: API lists authenticated user's active sessions")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_multiple_logins_create_multiple_sessions():
    client = create_test_client()

    first = register_account(
        client,
        "multi-session"
    )

    try:
        second_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": first["email"],
                "password": "StrongPassword123"
            }
        )

        if second_login.status_code != 200:
            raise ValueError(f"FAIL: Second login returned HTTP {second_login.status_code}: {second_login.text}")

        response = client.get(
            "/api/v1/auth/sessions",
            headers=auth_headers(
                first
            )
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Active session listing returned HTTP {response.status_code}: {response.text}")

        sessions = response.json()

        if len(sessions) != 2:
            raise ValueError(f"FAIL: Expected 2 active sessions but found {len(sessions)}")

        print("PASS: Multiple logins create separate sessions")

    finally:
        safe_delete_user(
            first["user_id"]
        )


def test_logout_all_revokes_every_session():
    client = create_test_client()

    first = register_account(
        client,
        "logout-all"
    )

    try:
        second_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": first["email"],
                "password": "StrongPassword123"
            }
        )

        if second_login.status_code != 200:
            raise ValueError(f"FAIL: Second login returned HTTP {second_login.status_code}: {second_login.text}")

        second = second_login.json()

        response = client.post(
            "/api/v1/auth/logout-all",
            headers=auth_headers(
                first
            )
        )

        if response.status_code != 204:
            raise ValueError(f"FAIL: logout-all returned HTTP {response.status_code}: {response.text}")

        first_me = client.get(
            "/api/v1/auth/me",
            headers=auth_headers(
                first
            )
        )

        second_me = client.get(
            "/api/v1/auth/me",
            headers=auth_headers(
                second
            )
        )

        if first_me.status_code != 401:
            raise ValueError(f"FAIL: First token returned HTTP {first_me.status_code} after logout-all")

        if second_me.status_code != 401:
            raise ValueError(f"FAIL: Second token returned HTTP {second_me.status_code} after logout-all")

        print("PASS: Logout-all revokes every active session")

    finally:
        safe_delete_user(
            first["user_id"]
        )


def test_session_listing_requires_authentication():
    client = create_test_client()

    response = client.get(
        "/api/v1/auth/sessions"
    )

    if response.status_code != 401:
        raise ValueError(f"FAIL: Session listing returned HTTP {response.status_code} instead of 401")

    print("PASS: Session listing requires authentication")


def test_logout_all_requires_authentication():
    client = create_test_client()

    response = client.post(
        "/api/v1/auth/logout-all"
    )

    if response.status_code != 401:
        raise ValueError(f"FAIL: Logout-all returned HTTP {response.status_code} instead of 401")

    print("PASS: Logout-all requires authentication")


def test_auth_hardening_routes_in_openapi():
    client = create_test_client()

    response = client.get(
        "/openapi.json"
    )

    if response.status_code != 200:
        raise ValueError(f"FAIL: OpenAPI returned HTTP {response.status_code}")

    schema = response.json()

    paths = schema[
        "paths"
    ]

    if "/api/v1/users" in paths:
        methods = paths[
            "/api/v1/users"
        ]

        if "post" in methods:
            raise ValueError("FAIL: Legacy POST /users still appears in OpenAPI")

    expected = {
        "/api/v1/auth/sessions",
        "/api/v1/auth/logout-all"
    }

    if not expected.issubset(
        set(
            paths.keys()
        )
    ):
        raise ValueError("FAIL: OpenAPI schema is missing authentication hardening routes")

    sessions_security = paths[
        "/api/v1/auth/sessions"
    ][
        "get"
    ].get(
        "security"
    )

    if not sessions_security:
        raise ValueError("FAIL: Session-list route is not documented as authenticated")

    logout_all_security = paths[
        "/api/v1/auth/logout-all"
    ][
        "post"
    ].get(
        "security"
    )

    if not logout_all_security:
        raise ValueError("FAIL: Logout-all route is not documented as authenticated")

    print("PASS: OpenAPI reflects hardened authentication routes")


if __name__ == "__main__":
    test_legacy_user_creation_removed()
    test_registered_user_has_active_session()
    test_multiple_logins_create_multiple_sessions()
    test_logout_all_revokes_every_session()
    test_session_listing_requires_authentication()
    test_logout_all_requires_authentication()
    test_auth_hardening_routes_in_openapi()