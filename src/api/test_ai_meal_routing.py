from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)

from src.rag.fake_llm_provider import (
    FakeLLMProvider
)


def create_conversation(client, account):
    response = client.post(
        "/api/v1/ai/conversations",
        headers=auth_headers(
            account
        ),
        json={
            "title": "Meal routing test"
        }
    )

    if response.status_code != 201:
        raise ValueError(f"FAIL: Could not create AI conversation: {response.text}")

    return response.json()


def test_meal_request_routes_to_deterministic_meal_system():
    provider = FakeLLMProvider(
        "This must not run because this new user has no nutrition target."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "meal-routing"
    )

    try:
        conversation = create_conversation(
            client,
            account
        )

        response = client.post(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(
                account
            ),
            json={
                "question": "Build me a meal"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Meal request returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["route"] != "nutrition":
            raise ValueError("FAIL: Meal request did not use nutrition route")

        if data["nutrition_action"]["action"] != "meal_generation":
            raise ValueError("FAIL: Meal request did not use deterministic meal-generation action")

        if data["status"] != "nutrition_target_missing":
            raise ValueError("FAIL: New user without nutrition target returned incorrect meal status")

        if provider.calls:
            raise ValueError("FAIL: Model was called despite missing deterministic nutrition target")

        print("PASS: AI API routes concrete meal request into deterministic nutrition engine")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_generic_macro_question_stays_nutrition_context():
    provider = FakeLLMProvider(
        "You do not currently have a stored nutrition target available to explain."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "macro-routing"
    )

    try:
        conversation = create_conversation(
            client,
            account
        )

        response = client.post(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(
                account
            ),
            json={
                "question": "What are my macros?"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Macro context request returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["nutrition_action"]["action"] != "nutrition_context":
            raise ValueError("FAIL: Macro explanation incorrectly triggered meal generation")

        if len(provider.calls) != 1:
            raise ValueError("FAIL: Generic nutrition explanation did not use context provider")

        print("PASS: Generic nutrition questions remain separate from meal generation")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_rejects_zero_meal_fraction():
    client = create_test_client(
        llm_provider=FakeLLMProvider(
            "Unused"
        )
    )

    account = register_account(
        client,
        "meal-fraction-zero"
    )

    try:
        conversation = create_conversation(
            client,
            account
        )

        response = client.post(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(
                account
            ),
            json={
                "question": "Build me a meal",
                "meal_fraction": 0
            }
        )

        if response.status_code != 422:
            raise ValueError(f"FAIL: Zero meal fraction returned HTTP {response.status_code}")

        print("PASS: AI API rejects zero meal fraction")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_rejects_meal_fraction_above_one():
    client = create_test_client(
        llm_provider=FakeLLMProvider(
            "Unused"
        )
    )

    account = register_account(
        client,
        "meal-fraction-high"
    )

    try:
        conversation = create_conversation(
            client,
            account
        )

        response = client.post(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(
                account
            ),
            json={
                "question": "Build me a meal",
                "meal_fraction": 1.5
            }
        )

        if response.status_code != 422:
            raise ValueError(f"FAIL: Excessive meal fraction returned HTTP {response.status_code}")

        print("PASS: AI API bounds requested meal fraction")

    finally:
        safe_delete_user(
            account["user_id"]
        )


if __name__ == "__main__":
    test_meal_request_routes_to_deterministic_meal_system()
    test_generic_macro_question_stays_nutrition_context()
    test_api_rejects_zero_meal_fraction()
    test_api_rejects_meal_fraction_above_one()