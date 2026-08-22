from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)

from src.rag.fake_llm_provider import (
    FakeLLMProvider
)

from src.rag.research_retriever import (
    get_research_corpus
)


def create_conversation(client, account):
    response = client.post(
        "/api/v1/ai/conversations",
        headers=auth_headers(
            account
        ),
        json={
            "title": "Routing test"
        }
    )

    if response.status_code != 201:
        raise ValueError("FAIL: Routing API test could not create conversation")

    return response.json()


def get_test_paper():
    papers = get_research_corpus()

    if not papers:
        raise ValueError("FAIL: Research database contains no papers")

    return papers[0]


def test_api_routes_research_message():
    paper = get_test_paper()

    provider = FakeLLMProvider(
        f"Research answer [{paper['paper_id']}]."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "routing-research"
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
                "question": paper["title"],
                "top_k": 1
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Research routing API returned HTTP {response.status_code}: {response.text}")

        if response.json()["route"] != "research":
            raise ValueError("FAIL: API did not route paper query to research")

        print("PASS: Conversation API automatically routes research questions")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_routes_coaching_message():
    provider = FakeLLMProvider(
        "Focus on completing the next planned action instead of making the session perfect."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "routing-coaching"
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
                "question": "Motivate me before training"
            }
        )

        if response.status_code != 200:
            raise ValueError("FAIL: Coaching routing API request failed")

        data = response.json()

        if data["route"] != "coaching":
            raise ValueError("FAIL: API did not route motivation message to coaching")

        if data["citations"]:
            raise ValueError("FAIL: Coaching API response returned research citations")

        print("PASS: Conversation API supports non-research coaching")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_routes_nutrition_message():
    provider = FakeLLMProvider(
        "I can explain the nutrition targets currently stored for your account."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "routing-nutrition"
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
            raise ValueError("FAIL: Nutrition routing API request failed")

        if response.json()["route"] != "nutrition":
            raise ValueError("FAIL: API did not route macro question to nutrition")

        print("PASS: Conversation API routes nutrition context separately")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_routes_safety_without_provider():
    provider = FakeLLMProvider(
        "This must never be called."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "routing-safety"
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
                "question": "My knee hurts when I squat"
            }
        )

        if response.status_code != 200:
            raise ValueError("FAIL: Safety routing API request failed")

        data = response.json()

        if data["route"] != "safety":
            raise ValueError("FAIL: API did not route pain message to safety")

        if provider.calls:
            raise ValueError("FAIL: API called model for deterministic safety response")

        print("PASS: Conversation API safety route bypasses model provider")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_api_routes_urgent_safety():
    provider = FakeLLMProvider(
        "Unused"
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "routing-urgent"
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
                "question": "I have chest pain while exercising"
            }
        )

        data = response.json()

        if data["routing"]["safety_level"] != "urgent":
            raise ValueError("FAIL: API lost urgent safety classification")

        if "Stop the exercise" not in data["answer"]:
            raise ValueError("FAIL: API urgent response omitted safety instruction")

        print("PASS: Conversation API preserves urgent safety classification")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_unknown_message_does_not_spend_provider_request():
    provider = FakeLLMProvider(
        "Unused"
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "routing-unknown"
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
                "question": "zzzxqvplmnkjhgfd"
            }
        )

        if response.status_code != 200:
            raise ValueError("FAIL: Unknown message request failed")

        if response.json()["route"] != "unknown":
            raise ValueError("FAIL: Unknown message returned incorrect route")

        if provider.calls:
            raise ValueError("FAIL: Unknown message consumed provider request")

        print("PASS: Unknown conversation input does not consume model quota")

    finally:
        safe_delete_user(
            account["user_id"]
        )


if __name__ == "__main__":
    test_api_routes_research_message()
    test_api_routes_coaching_message()
    test_api_routes_nutrition_message()
    test_api_routes_safety_without_provider()
    test_api_routes_urgent_safety()
    test_unknown_message_does_not_spend_provider_request()