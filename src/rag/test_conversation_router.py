from src.database.query_ai_conversation_database import (
    create_ai_conversation,
    get_ai_conversation_messages
)

from src.database.query_user_database import (
    create_user,
    delete_user
)

from src.rag.context_coaching_service import (
    validate_non_research_answer
)

from src.rag.conversation_router import (
    route_conversation_message
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

    return papers[0]


def test_research_route_uses_rag():
    user_id = create_user()

    try:
        paper = get_test_paper()

        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            f"Research answer [{paper['paper_id']}]."
        )

        result = route_conversation_message(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question=paper["title"],
            provider=provider,
            top_k=1
        )

        if result["route"] != "research":
            raise ValueError("FAIL: Research question did not use research route")

        if paper["paper_id"] not in result["citation_validation"]["cited_paper_ids"]:
            raise ValueError("FAIL: Research route lost citation validation")

        print("PASS: Research router preserves evidence-grounded RAG")

    finally:
        delete_user(
            user_id
        )


def test_coaching_route_calls_provider_without_rag_citations():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "Focus on showing up consistently and completing the session you planned."
        )

        result = route_conversation_message(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Motivate me before training",
            provider=provider
        )

        if result["route"] != "coaching":
            raise ValueError("FAIL: Coaching question did not use coaching route")

        if len(provider.calls) != 1:
            raise ValueError("FAIL: Coaching route did not call provider exactly once")

        if result["citations"]:
            raise ValueError("FAIL: Coaching route returned research citations")

        print("PASS: Coaching route works without pretending to use research evidence")

    finally:
        delete_user(
            user_id
        )


def test_personal_data_route_receives_user_context():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "I can summarize the stored training information available in your account."
        )

        result = route_conversation_message(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="Summarize my workout history",
            provider=provider
        )

        if result["route"] != "personal_data":
            raise ValueError("FAIL: Personal-data question used incorrect route")

        prompt = provider.calls[0]["user_prompt"]

        if "PERSONAL CONTEXT" not in prompt:
            raise ValueError("FAIL: Personal-data provider did not receive user context")

        if "VERIFIED ROUTE DATA" not in prompt:
            raise ValueError("FAIL: Personal-data provider did not receive verified analytics data")

        print("PASS: Personal-data route uses authenticated user context")

    finally:
        delete_user(
            user_id
        )


def test_nutrition_route_contains_hard_safety_rules():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "I can explain the nutrition targets currently stored for your account."
        )

        result = route_conversation_message(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="What are my macros?",
            provider=provider
        )

        if result["route"] != "nutrition":
            raise ValueError("FAIL: Nutrition message used incorrect route")

        if result["nutrition_action"]["action"] != "nutrition_context":
            raise ValueError("FAIL: Nutrition-context question unexpectedly triggered meal generation")

        if len(provider.calls) != 1:
            raise ValueError("FAIL: Nutrition context route did not call provider exactly once")

        system_prompt = provider.calls[0]["system_prompt"]

        if "Food allergies are hard safety constraints" not in system_prompt:
            raise ValueError("FAIL: Nutrition route omitted allergy safety rule")

        if "Do not create a specific meal or food plan" not in system_prompt:
            raise ValueError("FAIL: Nutrition context route allowed LLM-only meal generation")

        print("PASS: Nutrition AI remains subordinate to deterministic safety systems")

    finally:
        delete_user(
            user_id
        )


def test_safety_route_does_not_call_provider():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "This must not be generated."
        )

        result = route_conversation_message(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="My knee hurts when I squat",
            provider=provider
        )

        if result["status"] != "safety_response":
            raise ValueError("FAIL: Pain question did not produce safety response")

        if provider.calls:
            raise ValueError("FAIL: LLM provider was called for deterministic safety route")

        print("PASS: Safety route bypasses LLM generation")

    finally:
        delete_user(
            user_id
        )


def test_urgent_safety_route():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "Unused"
        )

        result = route_conversation_message(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="I have chest pain while exercising",
            provider=provider
        )

        if result["routing"]["safety_level"] != "urgent":
            raise ValueError("FAIL: Urgent safety signal lost urgency metadata")

        if "Stop the exercise" not in result["answer"]:
            raise ValueError("FAIL: Urgent safety response omitted stop-exercise instruction")

        print("PASS: Urgent safety routing returns deterministic escalation message")

    finally:
        delete_user(
            user_id
        )


def test_unknown_route_does_not_call_provider():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "Unused"
        )

        result = route_conversation_message(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="zzzxqvplmnkjhgfd",
            provider=provider
        )

        if result["route"] != "unknown":
            raise ValueError("FAIL: Gibberish input did not use unknown route")

        if provider.calls:
            raise ValueError("FAIL: Unknown route unnecessarily called provider")

        if result["status"] != "insufficient_evidence":
            raise ValueError("FAIL: Unknown route did not preserve safe no-evidence status")

        print("PASS: Unknown messages fail safely without spending model requests")

    finally:
        delete_user(
            user_id
        )


def test_safety_response_is_persisted():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        route_conversation_message(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question="My shoulder hurts",
            provider=FakeLLMProvider("Unused")
        )

        messages = get_ai_conversation_messages(
            user_id,
            conversation["conversation_id"],
            limit=20
        )

        if len(messages) != 2:
            raise ValueError("FAIL: Safety exchange was not persisted")

        if messages[-1]["retrieval_status"] != "safety:caution":
            raise ValueError("FAIL: Stored safety message lost routing status")

        print("PASS: Deterministic safety messages are persisted in conversation history")

    finally:
        delete_user(
            user_id
        )


def test_non_research_citation_is_rejected():
    try:
        validate_non_research_answer(
            "Here is unsupported evidence [P999]."
        )

    except ValueError:
        print("PASS: Non-research route rejects fabricated research citations")
        return

    raise ValueError("FAIL: Non-research route accepted research citation marker")


def test_coaching_provider_cannot_invent_citation():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "Stay consistent because research proves it [P999]."
        )

        try:
            route_conversation_message(
                user_id=user_id,
                conversation_id=conversation["conversation_id"],
                question="Motivate me",
                provider=provider
            )

        except ValueError as error:
            if "invented research citations" not in str(error):
                raise ValueError(f"FAIL: Wrong non-research citation error: {error}")

            print("PASS: Coaching model cannot fabricate evidence citations")
            return

        raise ValueError("FAIL: Coaching route accepted fabricated citation")

    finally:
        delete_user(
            user_id
        )


def test_research_intent_takes_precedence_over_nutrition():
    user_id = create_user()

    try:
        paper = get_test_paper()

        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            f"Evidence-based nutrition answer [{paper['paper_id']}]."
        )

        result = route_conversation_message(
            user_id=user_id,
            conversation_id=conversation["conversation_id"],
            question=paper["title"],
            provider=provider,
            top_k=1
        )

        if result["route"] != "research":
            raise ValueError("FAIL: Research intent was overridden by another route")

        print("PASS: Explicit research intent preserves RAG requirements")

    finally:
        delete_user(
            user_id
        )


if __name__ == "__main__":
    test_research_route_uses_rag()
    test_coaching_route_calls_provider_without_rag_citations()
    test_personal_data_route_receives_user_context()
    test_nutrition_route_contains_hard_safety_rules()
    test_safety_route_does_not_call_provider()
    test_urgent_safety_route()
    test_unknown_route_does_not_call_provider()
    test_safety_response_is_persisted()
    test_non_research_citation_is_rejected()
    test_coaching_provider_cannot_invent_citation()
    test_research_intent_takes_precedence_over_nutrition()