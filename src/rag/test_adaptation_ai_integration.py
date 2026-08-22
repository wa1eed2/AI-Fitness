from src.database.query_adaptation_database import (
    get_adaptation_proposal
)

from src.database.query_ai_conversation_database import (
    create_ai_conversation,
    get_ai_conversation_messages
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.database.setup_ai_conversation_database import (
    setup_ai_conversation_database
)

from src.rag.adaptation_tool_service import (
    generate_adaptation_conversation_answer
)

from src.rag.conversation_service import (
    ConversationNotFoundError
)

from src.rag.llm_provider import (
    LLMProviderUnavailableError
)


class RecordingProvider:
    def __init__(
        self,
        answer="The recorded signals support the deterministic adaptation result."
    ):
        self.answer = answer
        self.calls = 0
        self.system_prompt = None
        self.user_prompt = None

    def generate(
        self,
        system_prompt,
        user_prompt
    ):
        self.calls += 1
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt

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


def build_evaluation(
    user_id,
    action="progress_cautiously"
):
    if action == "progress_cautiously":
        reason_codes = [
            "SUFFICIENT_RECENT_TRAINING",
            "POSITIVE_EXERCISE_PROGRESSION",
            "NO_HIGH_EXERTION_SIGNAL"
        ]

    elif action == "reduce_volume":
        reason_codes = [
            "HIGH_RECENT_EXERTION_SIGNAL",
            "NEGATIVE_EXERCISE_PROGRESSION",
            "USER_CONFIRMATION_REQUIRED"
        ]

    elif action == "maintain":
        reason_codes = [
            "PROGRESSION_THRESHOLD_NOT_REACHED"
        ]

    else:
        reason_codes = [
            "PROFILE_REQUIRED"
        ]

    return {
        "user_id": user_id,
        "action": action,
        "reason_codes": reason_codes,
        "signals": {
            "completed_workout_count": 10,
            "exercise_log_coverage_percentage": 90.0,
            "recent_completion_ratio": 1.0,
            "progression": {
                "eligible_exercise_count": 3,
                "positive_progression_count": 2,
                "negative_progression_count": (
                    1
                    if action == "reduce_volume"
                    else 0
                )
            },
            "recovery": {
                "signal_status": (
                    "high_exertion"
                    if action == "reduce_volume"
                    else "normal"
                ),
                "high_exertion_signal": (
                    action == "reduce_volume"
                )
            }
        },
        "recommendation": {
            "change_type": (
                "training_progression"
                if action == "progress_cautiously"
                else "training_reduction"
                if action == "reduce_volume"
                else "none"
            ),
            "automatic_application": False,
            "requires_user_confirmation": (
                action in {
                    "progress_cautiously",
                    "reduce_volume"
                }
            )
        }
    }


def create_test_conversation():
    user_id = create_user()

    conversation = create_ai_conversation(
        user_id,
        title="Adaptation test"
    )

    return (
        user_id,
        conversation[
            "conversation_id"
        ]
    )


def test_conversation_ownership_checked_before_adaptation_tools():
    owner_id, conversation_id = create_test_conversation()
    other_user_id = create_user()

    evaluator_calls = {
        "count": 0
    }

    def evaluator(
        user_id,
        reference_date=None
    ):
        evaluator_calls[
            "count"
        ] += 1

        return build_evaluation(
            user_id
        )

    try:
        try:
            generate_adaptation_conversation_answer(
                user_id=other_user_id,
                conversation_id=conversation_id,
                question="Should I increase my training?",
                provider=RecordingProvider(),
                evaluator=evaluator
            )

        except ConversationNotFoundError:
            if evaluator_calls["count"] != 0:
                raise ValueError(
                    "FAIL: Adaptation analytics ran before ownership validation"
                )

            print("PASS: Adaptation conversation ownership is checked before analytics")
            return

        raise ValueError("FAIL: Cross-user adaptation conversation was accessible")

    finally:
        delete_user(
            owner_id
        )

        delete_user(
            other_user_id
        )


def test_insufficient_data_skips_provider_and_persists_proposal():
    user_id, conversation_id = create_test_conversation()

    provider = RecordingProvider()

    def evaluator(
        user_id,
        reference_date=None
    ):
        return build_evaluation(
            user_id,
            action="insufficient_data"
        )

    try:
        result = generate_adaptation_conversation_answer(
            user_id=user_id,
            conversation_id=conversation_id,
            question="Should I increase my training?",
            provider=provider,
            evaluator=evaluator
        )

        if provider.calls != 0:
            raise ValueError("FAIL: Provider was called for insufficient adaptation data")

        if result["action"] != "insufficient_data":
            raise ValueError("FAIL: Insufficient deterministic result was changed")

        if result["explanation_source"] != "deterministic":
            raise ValueError("FAIL: Insufficient-data response was not deterministic")

        proposal = get_adaptation_proposal(
            user_id,
            result[
                "proposal"
            ][
                "proposal_id"
            ]
        )

        if proposal is None:
            raise ValueError("FAIL: Insufficient-data adaptation record was not persisted")

        print("PASS: Insufficient adaptation data avoids provider quota and persists result")

    finally:
        delete_user(
            user_id
        )


def test_actionable_adaptation_uses_provider_as_explanation_only():
    user_id, conversation_id = create_test_conversation()

    provider = RecordingProvider()

    def evaluator(
        user_id,
        reference_date=None
    ):
        return build_evaluation(
            user_id,
            action="progress_cautiously"
        )

    try:
        result = generate_adaptation_conversation_answer(
            user_id=user_id,
            conversation_id=conversation_id,
            question="Should I increase my training?",
            provider=provider,
            evaluator=evaluator
        )

        if provider.calls != 1:
            raise ValueError("FAIL: Actionable adaptation did not call explanation provider once")

        if result["action"] != "progress_cautiously":
            raise ValueError("FAIL: Provider changed deterministic adaptation action")

        if result["applied"] is not False:
            raise ValueError("FAIL: AI adaptation conversation applied a training change")

        if result["explanation_source"] != "llm":
            raise ValueError("FAIL: Successful provider explanation source is incorrect")

        if "Do not claim that any training change has already been applied" not in provider.system_prompt:
            raise ValueError("FAIL: Adaptation prompt did not restrict write-authority claims")

        if "POSITIVE_EXERCISE_PROGRESSION" not in provider.user_prompt:
            raise ValueError("FAIL: Provider did not receive deterministic reason codes")

        print("PASS: AI provider explains deterministic adaptation without write authority")

    finally:
        delete_user(
            user_id
        )


def test_provider_outage_preserves_adaptation_result():
    user_id, conversation_id = create_test_conversation()

    provider = UnavailableProvider()

    def evaluator(
        user_id,
        reference_date=None
    ):
        return build_evaluation(
            user_id,
            action="reduce_volume"
        )

    try:
        result = generate_adaptation_conversation_answer(
            user_id=user_id,
            conversation_id=conversation_id,
            question="Should I reduce my training volume?",
            provider=provider,
            evaluator=evaluator
        )

        if provider.calls != 1:
            raise ValueError("FAIL: Provider outage fixture did not execute")

        if result["action"] != "reduce_volume":
            raise ValueError("FAIL: Provider outage destroyed deterministic adaptation result")

        if result["provider_available"] is not False:
            raise ValueError("FAIL: Provider outage was not exposed in result metadata")

        if result["explanation_source"] != "deterministic_fallback":
            raise ValueError("FAIL: Provider outage did not use deterministic fallback")

        if result["applied"] is not False:
            raise ValueError("FAIL: Provider fallback applied adaptation")

        if "not a medical diagnosis" not in result["answer"]:
            raise ValueError("FAIL: Reduction fallback lost safety framing")

        print("PASS: Deterministic adaptation survives AI-provider outage")

    finally:
        delete_user(
            user_id
        )


def test_adaptation_provider_cannot_fabricate_research_citation():
    user_id, conversation_id = create_test_conversation()

    provider = RecordingProvider(
        "The result is supported by research [P001]."
    )

    def evaluator(
        user_id,
        reference_date=None
    ):
        return build_evaluation(
            user_id,
            action="progress_cautiously"
        )

    try:
        try:
            generate_adaptation_conversation_answer(
                user_id=user_id,
                conversation_id=conversation_id,
                question="Am I ready to progress?",
                provider=provider,
                evaluator=evaluator
            )

        except ValueError as error:
            if "invented research citations" not in str(
                error
            ):
                raise ValueError(f"FAIL: Wrong citation validation error: {error}")

            print("PASS: Adaptation explanation cannot fabricate research citations")
            return

        raise ValueError("FAIL: Fabricated adaptation citation was accepted")

    finally:
        delete_user(
            user_id
        )


def test_adaptation_exchange_is_persisted():
    user_id, conversation_id = create_test_conversation()

    provider = RecordingProvider()

    def evaluator(
        user_id,
        reference_date=None
    ):
        return build_evaluation(
            user_id,
            action="maintain"
        )

    try:
        result = generate_adaptation_conversation_answer(
            user_id=user_id,
            conversation_id=conversation_id,
            question="How is my recovery looking?",
            provider=provider,
            evaluator=evaluator
        )

        messages = get_ai_conversation_messages(
            user_id,
            conversation_id,
            limit=8
        )

        if messages is None or len(messages) < 2:
            raise ValueError("FAIL: Adaptation conversation exchange was not persisted")

        assistant_messages = [
            message
            for message in messages
            if message.get(
                "role"
            ) == "assistant"
        ]

        if not assistant_messages:
            raise ValueError("FAIL: Persisted adaptation exchange has no assistant message")

        if result["answer"] not in [
            message.get(
                "content"
            )
            for message in assistant_messages
        ]:
            raise ValueError("FAIL: Persisted adaptation answer does not match result")

        print("PASS: Adaptation explanation is persisted in AI conversation history")

    finally:
        delete_user(
            user_id
        )


if __name__ == "__main__":
    setup_ai_conversation_database()

    test_conversation_ownership_checked_before_adaptation_tools()
    test_insufficient_data_skips_provider_and_persists_proposal()
    test_actionable_adaptation_uses_provider_as_explanation_only()
    test_provider_outage_preserves_adaptation_result()
    test_adaptation_provider_cannot_fabricate_research_citation()
    test_adaptation_exchange_is_persisted()