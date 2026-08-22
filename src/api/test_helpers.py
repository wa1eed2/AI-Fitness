from uuid import uuid4


from fastapi.testclient import (
    TestClient
)


from src.api.app import (
    create_app
)

from src.database.query_user_database import (
    delete_user
)


TEST_PASSWORD = "StrongPassword123"


def create_test_client(
    llm_provider=None,
    vision_analyzer=None,
    vision_model_path=None
):
    return TestClient(
        create_app(
            llm_provider=llm_provider,
            vision_analyzer=vision_analyzer,
            vision_model_path=vision_model_path
        )
    )


def unique_email(
    prefix="test"
):
    return (
        f"{prefix}-{uuid4().hex}@example.com"
    )


def register_account(
    client,
    prefix="test",
    password=TEST_PASSWORD
):
    email = unique_email(
        prefix
    )

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password
        }
    )

    if response.status_code != 201:
        raise ValueError(
            f"FAIL: Test account registration failed: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


def auth_headers(
    account
):
    return {
        "Authorization": (
            f"Bearer {account['access_token']}"
        )
    }


def safe_delete_user(
    user_id
):
    try:
        delete_user(
            user_id
        )

    except Exception:
        pass