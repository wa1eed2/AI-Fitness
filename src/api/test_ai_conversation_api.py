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


def get_test_paper():
    papers = get_research_corpus()

    if not papers:
        raise ValueError("FAIL: Research database contains no papers")

    return papers[
        0
    ]


def create_conversation(client, account, title="Test conversation"):
    response = client.post(
        "/api/v1/ai/conversations",
        headers=auth_headers(
            account
        ),
        json={
            "title": title
        }
    )

    if response.status_code != 201:
        raise ValueError(f"FAIL: Conversation setup failed: {response.status_code} {response.text}")

    return response.json()


def test_conversation_creation_requires_authentication():
    client = create_test_client(
        llm_provider=FakeLLMProvider(
            "Unused"
        )
    )

    response = client.post(
        "/api/v1/ai/conversations",
        json={
            "title": "Private conversation"
        }
    )

    if response.status_code != 401:
        raise ValueError(f"FAIL: Unauthenticated conversation creation returned HTTP {response.status_code}")

    print("PASS: AI conversation creation requires authentication")


def test_authenticated_user_can_create_and_list_conversations():
    client = create_test_client(
        llm_provider=FakeLLMProvider(
            "Unused"
        )
    )

    account = register_account(
        client,
        "conversation-list"
    )

    try:
        conversation = create_conversation(
            client,
            account,
            "My AI Coach"
        )

        response = client.get(
            "/api/v1/ai/conversations",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 200:
            raise ValueError("FAIL: Conversation list request failed")

        conversations = response.json()

        if len(conversations) != 1:
            raise ValueError("FAIL: Conversation list returned incorrect count")

        if conversations[0]["conversation_id"] != conversation["conversation_id"]:
            raise ValueError("FAIL: Conversation list returned incorrect conversation")

        print("PASS: Authenticated user can create and list AI conversations")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_authenticated_user_can_get_own_conversation():
    client = create_test_client(
        llm_provider=FakeLLMProvider(
            "Unused"
        )
    )

    account = register_account(
        client,
        "conversation-get"
    )

    try:
        conversation = create_conversation(
            client,
            account
        )

        response = client.get(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 200:
            raise ValueError("FAIL: User could not retrieve own conversation")

        print("PASS: Authenticated user can retrieve own AI conversation")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_cross_user_conversation_access_returns_404():
    client = create_test_client(
        llm_provider=FakeLLMProvider(
            "Unused"
        )
    )

    owner = register_account(
        client,
        "conversation-owner"
    )

    other = register_account(
        client,
        "conversation-other"
    )

    try:
        conversation = create_conversation(
            client,
            owner
        )

        response = client.get(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}",
            headers=auth_headers(
                other
            )
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Cross-user conversation access returned HTTP {response.status_code}")

        print("PASS: AI conversation API hides cross-user conversations")

    finally:
        safe_delete_user(
            owner[
                "user_id"
            ]
        )

        safe_delete_user(
            other[
                "user_id"
            ]
        )


def test_conversation_can_be_renamed():
    client = create_test_client(
        llm_provider=FakeLLMProvider(
            "Unused"
        )
    )

    account = register_account(
        client,
        "conversation-rename"
    )

    try:
        conversation = create_conversation(
            client,
            account
        )

        response = client.patch(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}",
            headers=auth_headers(
                account
            ),
            json={
                "title": "Updated AI Coach"
            }
        )

        if response.status_code != 200:
            raise ValueError("FAIL: Conversation rename failed")

        if response.json()["title"] != "Updated AI Coach":
            raise ValueError("FAIL: Conversation API returned incorrect updated title")

        print("PASS: AI conversation title can be updated through API")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_conversation_message_generates_and_persists_answer():
    paper = get_test_paper()

    provider = FakeLLMProvider(
        f"Evidence-grounded conversation answer [{paper['paper_id']}]."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "conversation-message"
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
                "question": paper[
                    "title"
                ],
                "top_k": 1
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Conversation generation returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["status"] != "generated":
            raise ValueError("FAIL: Conversation API did not return generated status")

        if data["assistant_message"]["role"] != "assistant":
            raise ValueError("FAIL: Conversation API did not return persisted assistant message")

        print("PASS: AI conversation endpoint generates and persists grounded answer")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_conversation_messages_can_be_retrieved():
    paper = get_test_paper()

    provider = FakeLLMProvider(
        f"Stored answer [{paper['paper_id']}]."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "conversation-history"
    )

    try:
        conversation = create_conversation(
            client,
            account
        )

        client.post(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(
                account
            ),
            json={
                "question": paper[
                    "title"
                ],
                "top_k": 1
            }
        )

        response = client.get(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 200:
            raise ValueError("FAIL: Conversation message history request failed")

        messages = response.json()

        if len(messages) != 2:
            raise ValueError("FAIL: Conversation API returned incorrect message count")

        if messages[0]["role"] != "user" or messages[1]["role"] != "assistant":
            raise ValueError("FAIL: Conversation API returned incorrect message order")

        print("PASS: AI conversation history can be retrieved")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_no_evidence_does_not_call_provider():
    provider = FakeLLMProvider(
        "This response must not be used."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "conversation-no-evidence"
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
            raise ValueError("FAIL: No-evidence conversation request failed")

        if response.json()["status"] != "insufficient_evidence":
            raise ValueError("FAIL: No-evidence conversation returned incorrect status")

        if provider.calls:
            raise ValueError("FAIL: Provider was called without current research evidence")

        print("PASS: Conversation API does not use AI when research evidence is unavailable")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_cross_user_message_generation_returns_404():
    paper = get_test_paper()

    provider = FakeLLMProvider(
        f"Answer [{paper['paper_id']}]."
    )

    client = create_test_client(
        llm_provider=provider
    )

    owner = register_account(
        client,
        "message-owner"
    )

    other = register_account(
        client,
        "message-other"
    )

    try:
        conversation = create_conversation(
            client,
            owner
        )

        response = client.post(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}/messages",
            headers=auth_headers(
                other
            ),
            json={
                "question": paper[
                    "title"
                ],
                "top_k": 1
            }
        )

        if response.status_code != 404:
            raise ValueError(f"FAIL: Cross-user AI message returned HTTP {response.status_code}")

        if provider.calls:
            raise ValueError("FAIL: Provider was called before ownership validation")

        print("PASS: Conversation message generation enforces authenticated ownership")

    finally:
        safe_delete_user(
            owner[
                "user_id"
            ]
        )

        safe_delete_user(
            other[
                "user_id"
            ]
        )


def test_conversation_can_be_deleted():
    client = create_test_client(
        llm_provider=FakeLLMProvider(
            "Unused"
        )
    )

    account = register_account(
        client,
        "conversation-delete"
    )

    try:
        conversation = create_conversation(
            client,
            account
        )

        response = client.delete(
            f"/api/v1/ai/conversations/{conversation['conversation_id']}",
            headers=auth_headers(
                account
            )
        )

        if response.status_code != 200:
            raise ValueError("FAIL: Conversation deletion failed")

        if not response.json()["deleted"]:
            raise ValueError("FAIL: Conversation deletion returned incorrect result")

        print("PASS: Authenticated user can delete own AI conversation")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_conversation_routes_appear_in_openapi():
    client = create_test_client(
        llm_provider=FakeLLMProvider(
            "Unused"
        )
    )

    schema = client.get(
        "/openapi.json"
    ).json()

    paths = schema[
        "paths"
    ]

    required_paths = [
        "/api/v1/ai/conversations",
        "/api/v1/ai/conversations/{conversation_id}",
        "/api/v1/ai/conversations/{conversation_id}/messages"
    ]

    for path in required_paths:
        if path not in paths:
            raise ValueError(f"FAIL: OpenAPI schema is missing AI conversation route: {path}")

    create_operation = paths[
        "/api/v1/ai/conversations"
    ][
        "post"
    ]

    if not create_operation.get(
        "security"
    ):
        raise ValueError("FAIL: AI conversation routes are not documented as authenticated")

    print("PASS: OpenAPI documents authenticated AI conversation routes")


if __name__ == "__main__":
    test_conversation_creation_requires_authentication()
    test_authenticated_user_can_create_and_list_conversations()
    test_authenticated_user_can_get_own_conversation()
    test_cross_user_conversation_access_returns_404()
    test_conversation_can_be_renamed()
    test_conversation_message_generates_and_persists_answer()
    test_conversation_messages_can_be_retrieved()
    test_no_evidence_does_not_call_provider()
    test_cross_user_message_generation_returns_404()
    test_conversation_can_be_deleted()
    test_conversation_routes_appear_in_openapi()