from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)

from src.database.query_user_database import (
    create_user_profile
)

from src.rag.fake_llm_provider import (
    FakeLLMProvider
)

from src.rag.research_retriever import (
    get_research_corpus
)


def valid_profile():
    return {
        "age": 25,
        "sex": "Male",
        "height_cm": 180,
        "weight_kg": 80,
        "fitness_level": "Intermediate",
        "primary_goal": "Strength",
        "training_days_per_week": 4,
        "session_duration_minutes": 60,
        "preferred_environment": "Gym"
    }


def get_test_paper():
    papers = get_research_corpus()

    if not papers:
        raise ValueError("FAIL: Research database contains no papers")

    return papers[
        0
    ]


def build_provider_for_paper(
    paper
):
    return FakeLLMProvider(
        f"The retrieved research supports an evidence-grounded answer [{paper['paper_id']}]."
    )


def test_ai_route_requires_authentication():
    paper = get_test_paper()

    provider = build_provider_for_paper(
        paper
    )

    client = create_test_client(
        llm_provider=provider
    )

    response = client.post(
        "/api/v1/ai/research-answer",
        json={
            "question": paper["title"],
            "top_k": 1
        }
    )

    if response.status_code != 401:
        raise ValueError(f"FAIL: Unauthenticated AI request returned HTTP {response.status_code} instead of 401")

    if provider.calls:
        raise ValueError("FAIL: AI provider was called before authentication succeeded")

    print("PASS: AI research endpoint requires authentication")


def test_authenticated_ai_answer_generation():
    paper = get_test_paper()

    provider = build_provider_for_paper(
        paper
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-answer"
    )

    try:
        response = client.post(
            "/api/v1/ai/research-answer",
            headers=auth_headers(
                account
            ),
            json={
                "question": paper["title"],
                "top_k": 1
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Authenticated AI request returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["status"] != "generated":
            raise ValueError("FAIL: AI endpoint did not return generated status")

        if paper["paper_id"] not in data["citation_validation"]["cited_paper_ids"]:
            raise ValueError("FAIL: AI endpoint did not validate research citation")

        print("PASS: Authenticated AI endpoint generates evidence-backed answer")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_ai_endpoint_uses_authenticated_user_context():
    paper = get_test_paper()

    provider = build_provider_for_paper(
        paper
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-context"
    )

    try:
        create_user_profile(
            account["user_id"],
            valid_profile()
        )

        response = client.post(
            "/api/v1/ai/research-answer",
            headers=auth_headers(
                account
            ),
            json={
                "question": paper["title"],
                "top_k": 1
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: User-context AI request returned HTTP {response.status_code}: {response.text}")

        if len(provider.calls) != 1:
            raise ValueError("FAIL: AI provider was not called exactly once")

        prompt = provider.calls[
            0
        ][
            "user_prompt"
        ]

        if '"primary_goal": "Strength"' not in prompt:
            raise ValueError("FAIL: AI route did not use authenticated user's profile")

        print("PASS: AI endpoint derives personalization from authenticated identity")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_ai_response_does_not_expose_full_user_context():
    paper = get_test_paper()

    provider = build_provider_for_paper(
        paper
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-private-context"
    )

    try:
        create_user_profile(
            account["user_id"],
            valid_profile()
        )

        response = client.post(
            "/api/v1/ai/research-answer",
            headers=auth_headers(
                account
            ),
            json={
                "question": paper["title"],
                "top_k": 1
            }
        )

        data = response.json()

        if "user_context" in data:
            raise ValueError("FAIL: AI API exposed complete personal user context")

        if "user_context_summary" not in data:
            raise ValueError("FAIL: AI API omitted safe context summary")

        print("PASS: AI API does not echo complete personal context")

    finally:
        safe_delete_user(
            account["user_id"]
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
        "ai-no-evidence"
    )

    try:
        response = client.post(
            "/api/v1/ai/research-answer",
            headers=auth_headers(
                account
            ),
            json={
                "question": "zzzxqvplmnkjhgfd"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: No-evidence AI request returned HTTP {response.status_code}: {response.text}")

        if response.json()["status"] != "insufficient_evidence":
            raise ValueError("FAIL: No-evidence AI request returned incorrect status")

        if provider.calls:
            raise ValueError("FAIL: AI provider was called without relevant research evidence")

        print("PASS: AI API fails safely without relevant research evidence")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_ai_rejects_invalid_threshold_order():
    paper = get_test_paper()

    provider = build_provider_for_paper(
        paper
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-threshold"
    )

    try:
        response = client.post(
            "/api/v1/ai/research-answer",
            headers=auth_headers(
                account
            ),
            json={
                "question": paper["title"],
                "min_relevance_score": 0.5,
                "strong_relevance_score": 0.2
            }
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Invalid threshold ordering returned HTTP {response.status_code} instead of 400")

        if provider.calls:
            raise ValueError("FAIL: Provider was called for invalid threshold configuration")

        print("PASS: AI API validates relevance-threshold ordering")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_ai_rejects_invalid_year_range():
    paper = get_test_paper()

    provider = build_provider_for_paper(
        paper
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-years"
    )

    try:
        response = client.post(
            "/api/v1/ai/research-answer",
            headers=auth_headers(
                account
            ),
            json={
                "question": paper["title"],
                "min_year": 2030,
                "max_year": 2020
            }
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Invalid year range returned HTTP {response.status_code} instead of 400")

        print("PASS: AI API validates research year range")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_ai_schema_rejects_invalid_top_k():
    paper = get_test_paper()

    provider = build_provider_for_paper(
        paper
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-top-k"
    )

    try:
        response = client.post(
            "/api/v1/ai/research-answer",
            headers=auth_headers(
                account
            ),
            json={
                "question": paper["title"],
                "top_k": 0
            }
        )

        if response.status_code != 422:
            raise ValueError(f"FAIL: Invalid top_k returned HTTP {response.status_code} instead of 422")

        print("PASS: AI API schema rejects invalid top_k")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_ai_blocks_hallucinated_citation():
    paper = get_test_paper()

    provider = FakeLLMProvider(
        "Invented evidence [P999]."
    )

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-bad-citation"
    )

    try:
        response = client.post(
            "/api/v1/ai/research-answer",
            headers=auth_headers(
                account
            ),
            json={
                "question": paper["title"],
                "top_k": 1
            }
        )

        if response.status_code != 400:
            raise ValueError(f"FAIL: Hallucinated citation returned HTTP {response.status_code} instead of 400")

        if "unsupported citations" not in response.json()["detail"]:
            raise ValueError("FAIL: AI API returned incorrect hallucinated-citation error")

        print("PASS: AI API blocks hallucinated research citations")

    finally:
        safe_delete_user(
            account["user_id"]
        )


def test_ai_route_appears_in_openapi():
    client = create_test_client(
        llm_provider=FakeLLMProvider(
            "Unused"
        )
    )

    schema = client.get(
        "/openapi.json"
    ).json()

    path = "/api/v1/ai/research-answer"

    if path not in schema["paths"]:
        raise ValueError("FAIL: OpenAPI schema is missing AI research endpoint")

    operation = schema[
        "paths"
    ][
        path
    ][
        "post"
    ]

    if not operation.get(
        "security"
    ):
        raise ValueError("FAIL: AI endpoint is not documented as authenticated")

    print("PASS: OpenAPI documents authenticated AI research endpoint")


if __name__ == "__main__":
    test_ai_route_requires_authentication()
    test_authenticated_ai_answer_generation()
    test_ai_endpoint_uses_authenticated_user_context()
    test_ai_response_does_not_expose_full_user_context()
    test_no_evidence_does_not_call_provider()
    test_ai_rejects_invalid_threshold_order()
    test_ai_rejects_invalid_year_range()
    test_ai_schema_rejects_invalid_top_k()
    test_ai_blocks_hallucinated_citation()
    test_ai_route_appears_in_openapi()