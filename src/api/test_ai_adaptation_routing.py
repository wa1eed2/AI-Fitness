import src.rag.adaptation_tool_service as adaptation_tool_service

from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)

from src.rag.llm_provider import (
    LLMProviderUnavailableError
)


class CountingProvider:
    def __init__(
        self,
        answer="The deterministic training signals explain the current result."
    ):
        self.answer = answer
        self.calls = 0

    def generate(
        self,
        system_prompt,
        user_prompt
    ):
        self.calls += 1

        return self.answer


class UnavailableProvider:
    def __init__(self):
        self.calls = 0

    def generate(
        self,
        system_prompt,
        user_prompt
    ):
        self.calls += 1

        raise LLMProviderUnavailableError(
            "Provider temporarily unavailable"
        )


def create_conversation(
    client,
    account
):
    response = client.post(
        "/api/v1/ai/conversations",
        headers=auth_headers(
            account
        ),
        json={
            "title": "Adaptation routing"
        }
    )

    if response.status_code != 201:
        raise ValueError(f"FAIL: Could not create AI conversation: {response.text}")

    return response.json()


def fake_actionable_evaluation(
    user_id,
    reference_date=None
):
    return {
        "user_id": user_id,
        "action": "progress_cautiously",
        "reason_codes": [
            "SUFFICIENT_RECENT_TRAINING",
            "POSITIVE_EXERCISE_PROGRESSION",
            "NO_HIGH_EXERTION_SIGNAL"
        ],
        "signals": {
            "completed_workout_count": 10,
            "exercise_log_coverage_percentage": 90.0,
            "recent_completion_ratio": 1.0,
            "progression": {
                "eligible_exercise_count": 3,
                "positive_progression_count": 2,
                "negative_progression_count": 0
            },
            "recovery": {
                "signal_status": "normal",
                "high_exertion_signal": False
            }
        },
        "recommendation": {
            "change_type": "training_progression",
            "automatic_application": False,
            "requires_user_confirmation": True
        }
    }


def test_ai_api_routes_adaptation_question_without_model_when_data_missing():
    provider = CountingProvider()

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-adaptation-missing-data"
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
                "question": "Should I increase my training?"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: AI adaptation routing returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["route"] != "adaptation":
            raise ValueError(f"FAIL: Adaptation question routed to {data['route']}")

        if data["action"] != "insufficient_data":
            raise ValueError("FAIL: User without profile did not receive insufficient-data result")

        if provider.calls != 0:
            raise ValueError("FAIL: Provider quota was spent on insufficient adaptation data")

        if data["applied"] is not False:
            raise ValueError("FAIL: AI adaptation route silently modified training")

        print("PASS: AI API routes adaptation and avoids provider use when data is insufficient")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_ai_adaptation_proposal_is_available_through_adaptation_api():
    provider = CountingProvider()

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-adaptation-persistence"
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
                "question": "How is my recovery looking?"
            }
        )

        if response.status_code != 200:
            raise ValueError("FAIL: Adaptation conversation request failed")

        result = response.json()

        proposal_id = result[
            "proposal"
        ][
            "proposal_id"
        ]

        proposal_response = client.get(
            f"/api/v1/adaptations/{proposal_id}",
            headers=auth_headers(
                account
            )
        )

        if proposal_response.status_code != 200:
            raise ValueError("FAIL: AI-created adaptation proposal is not accessible through adaptation API")

        proposal = proposal_response.json()

        if proposal["proposal_id"] != proposal_id:
            raise ValueError("FAIL: Adaptation API returned wrong AI-created proposal")

        if proposal["status"] != "pending":
            raise ValueError("FAIL: AI-created proposal was not left pending")

        print("PASS: AI-generated deterministic adaptation proposal uses existing proposal workflow")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_safety_precedence_blocks_adaptation_tools():
    provider = CountingProvider()

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-adaptation-safety"
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
                "question": "My knee hurts; should I increase my training?"
            }
        )

        if response.status_code != 200:
            raise ValueError("FAIL: Safety-priority adaptation request failed")

        data = response.json()

        if data["route"] != "safety":
            raise ValueError("FAIL: Adaptation route overrode safety routing")

        if provider.calls != 0:
            raise ValueError("FAIL: Safety-priority message consumed provider quota")

        proposals = client.get(
            "/api/v1/adaptations",
            headers=auth_headers(
                account
            )
        )

        if proposals.status_code != 200:
            raise ValueError("FAIL: Could not inspect adaptation proposals")

        if proposals.json():
            raise ValueError("FAIL: Safety-priority message created adaptation proposal")

        print("PASS: AI safety routing takes precedence over adaptation evaluation")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_ai_adaptation_survives_provider_outage():
    provider = UnavailableProvider()

    client = create_test_client(
        llm_provider=provider
    )

    account = register_account(
        client,
        "ai-adaptation-provider-fallback"
    )

    original_evaluator = (
        adaptation_tool_service.evaluate_training_adaptation
    )

    adaptation_tool_service.evaluate_training_adaptation = (
        fake_actionable_evaluation
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
                "question": "Am I ready to progress?"
            }
        )

        if response.status_code != 200:
            raise ValueError(f"FAIL: Provider outage adaptation returned HTTP {response.status_code}: {response.text}")

        data = response.json()

        if data["route"] != "adaptation":
            raise ValueError("FAIL: Provider outage changed adaptation routing")

        if data["action"] != "progress_cautiously":
            raise ValueError("FAIL: Provider outage changed deterministic adaptation result")

        if data["provider_available"] is not False:
            raise ValueError("FAIL: Provider outage metadata is incorrect")

        if data["explanation_source"] != "deterministic_fallback":
            raise ValueError("FAIL: Provider outage did not return deterministic explanation")

        if data["proposal"]["status"] != "pending":
            raise ValueError("FAIL: Provider outage destroyed pending proposal")

        if data["applied"] is not False:
            raise ValueError("FAIL: Provider outage caused adaptation application")

        print("PASS: AI adaptation API preserves deterministic proposal during provider outage")

    finally:
        adaptation_tool_service.evaluate_training_adaptation = (
            original_evaluator
        )

        safe_delete_user(
            account[
                "user_id"
            ]
        )


if __name__ == "__main__":
    test_ai_api_routes_adaptation_question_without_model_when_data_missing()
    test_ai_adaptation_proposal_is_available_through_adaptation_api()
    test_safety_precedence_blocks_adaptation_tools()
    test_ai_adaptation_survives_provider_outage()