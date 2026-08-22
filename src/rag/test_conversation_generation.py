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

from src.rag.conversation_prompt_builder import (
    build_conversation_generation_prompts,
    build_conversation_history
)

from src.rag.conversation_service import (
    ConversationNotFoundError,
    generate_conversation_research_answer
)

from src.rag.fake_llm_provider import (
    FakeLLMProvider
)

from src.rag.rag_service import (
    prepare_research_rag
)

from src.rag.research_retriever import (
    get_research_corpus
)

from src.rag.user_context import (
    build_user_context
)


class SequentialFakeLLMProvider:
    def __init__(self, responses):
        self.responses = list(
            responses
        )

        self.calls = []

    def generate(
        self,
        system_prompt,
        user_prompt
    ):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            }
        )

        if not self.responses:
            raise ValueError("No fake responses remaining")

        return self.responses.pop(
            0
        )


def get_test_paper():
    papers = get_research_corpus()

    if not papers:
        raise ValueError("FAIL: Research database contains no papers")

    return papers[
        0
    ]


def test_empty_conversation_history():
    history = build_conversation_history(
        []
    )

    if history != "No prior conversation.":
        raise ValueError("FAIL: Empty conversation history returned unexpected text")

    print("PASS: Empty conversation history is explicit")


def test_conversation_history_is_bounded():
    messages = [
        {
            "role": "user",
            "content": "A" * 500
        },
        {
            "role": "assistant",
            "content": "B" * 500
        }
    ]

    history = build_conversation_history(
        messages,
        max_chars=300
    )

    if len(history) > 300:
        raise ValueError("FAIL: Conversation history exceeded character budget")

    print("PASS: Conversation history respects character budget")


def test_prompt_contains_history_and_current_evidence():
    user_id = create_user()

    try:
        paper = get_test_paper()

        prepared = prepare_research_rag(
            paper["title"],
            top_k=1
        )

        user_context = build_user_context(
            user_id
        )

        prompts = build_conversation_generation_prompts(
            prepared,
            user_context,
            [
                {
                    "role": "user",
                    "content": "Earlier question"
                },
                {
                    "role": "assistant",
                    "content": "Earlier answer"
                }
            ]
        )

        if "Earlier question" not in prompts["user_prompt"]:
            raise ValueError("FAIL: Conversation prompt omitted history")

        if paper["title"] not in prompts["user_prompt"]:
            raise ValueError("FAIL: Conversation prompt omitted current research evidence")

        print("PASS: Conversation prompt combines continuity with fresh research evidence")

    finally:
        delete_user(
            user_id
        )


def test_prompt_marks_history_as_non_evidence():
    user_id = create_user()

    try:
        paper = get_test_paper()

        prepared = prepare_research_rag(
            paper["title"],
            top_k=1
        )

        prompts = build_conversation_generation_prompts(
            prepared,
            build_user_context(
                user_id
            ),
            []
        )

        required = [
            "Previous user messages are not scientific evidence",
            "Previous assistant messages are not scientific evidence",
            "Only the CURRENT RESEARCH EVIDENCE section"
        ]

        for phrase in required:
            if phrase not in prompts["system_prompt"]:
                raise ValueError(f"FAIL: Conversation grounding rule missing: {phrase}")

        print("PASS: Conversation history is explicitly separated from evidence")

    finally:
        delete_user(
            user_id
        )


def test_generated_exchange_is_persisted():
    user_id = create_user()

    try:
        paper = get_test_paper()

        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            f"Grounded answer [{paper['paper_id']}]."
        )

        result = generate_conversation_research_answer(
            user_id=user_id,
            conversation_id=conversation[
                "conversation_id"
            ],
            question=paper[
                "title"
            ],
            provider=provider,
            top_k=1
        )

        messages = get_ai_conversation_messages(
            user_id,
            conversation[
                "conversation_id"
            ],
            limit=20
        )

        if result["status"] != "generated":
            raise ValueError("FAIL: Conversation answer did not generate")

        if len(messages) != 2:
            raise ValueError("FAIL: Generated conversation exchange was not persisted")

        print("PASS: Generated AI conversation exchange is persisted")

    finally:
        delete_user(
            user_id
        )


def test_second_turn_receives_previous_history():
    user_id = create_user()

    try:
        paper = get_test_paper()

        conversation = create_ai_conversation(
            user_id
        )

        first_provider = FakeLLMProvider(
            f"First answer [{paper['paper_id']}]."
        )

        generate_conversation_research_answer(
            user_id=user_id,
            conversation_id=conversation[
                "conversation_id"
            ],
            question=paper[
                "title"
            ],
            provider=first_provider,
            top_k=1
        )

        second_provider = FakeLLMProvider(
            f"Second answer [{paper['paper_id']}]."
        )

        result = generate_conversation_research_answer(
            user_id=user_id,
            conversation_id=conversation[
                "conversation_id"
            ],
            question=paper[
                "title"
            ],
            provider=second_provider,
            top_k=1
        )

        prompt = second_provider.calls[
            0
        ][
            "user_prompt"
        ]

        if "First answer" not in prompt:
            raise ValueError("FAIL: Second turn did not receive previous assistant history")

        if result["history_message_count"] != 2:
            raise ValueError("FAIL: Conversation service reported incorrect history count")

        print("PASS: Later conversation turns receive bounded previous history")

    finally:
        delete_user(
            user_id
        )


def test_no_evidence_is_stored_without_provider_call():
    user_id = create_user()

    try:
        conversation = create_ai_conversation(
            user_id
        )

        provider = FakeLLMProvider(
            "This response must never be used."
        )

        result = generate_conversation_research_answer(
            user_id=user_id,
            conversation_id=conversation[
                "conversation_id"
            ],
            question="zzzxqvplmnkjhgfd",
            provider=provider
        )

        messages = get_ai_conversation_messages(
            user_id,
            conversation[
                "conversation_id"
            ],
            limit=20
        )

        if provider.calls:
            raise ValueError("FAIL: Provider was called without research evidence")

        if result["status"] != "insufficient_evidence":
            raise ValueError("FAIL: Conversation returned incorrect no-evidence status")

        if len(messages) != 2:
            raise ValueError("FAIL: Safe no-evidence exchange was not persisted")

        print("PASS: No-evidence conversation response is stored without model call")

    finally:
        delete_user(
            user_id
        )


def test_historical_fake_citation_cannot_become_current_evidence():
    user_id = create_user()

    try:
        paper = get_test_paper()

        conversation = create_ai_conversation(
            user_id
        )

        first_provider = FakeLLMProvider(
            f"Valid first answer [{paper['paper_id']}]."
        )

        generate_conversation_research_answer(
            user_id=user_id,
            conversation_id=conversation[
                "conversation_id"
            ],
            question=paper[
                "title"
            ],
            provider=first_provider,
            top_k=1
        )

        provider = SequentialFakeLLMProvider(
            [
                "Historical citation should not work [P999].",
                "Still invalid [P999]."
            ]
        )

        try:
            generate_conversation_research_answer(
                user_id=user_id,
                conversation_id=conversation[
                    "conversation_id"
                ],
                question=paper[
                    "title"
                ],
                provider=provider,
                top_k=1
            )

        except ValueError:
            if len(provider.calls) != 2:
                raise ValueError("FAIL: Invalid current citation did not use bounded repair")

            print("PASS: Historical citation cannot bypass current retrieval allowlist")
            return

        raise ValueError("FAIL: Historical fabricated citation was accepted")

    finally:
        delete_user(
            user_id
        )


def test_repaired_answer_is_persisted():
    user_id = create_user()

    try:
        paper = get_test_paper()

        conversation = create_ai_conversation(
            user_id
        )

        provider = SequentialFakeLLMProvider(
            [
                "Draft without citation.",
                f"Repaired answer [{paper['paper_id']}]."
            ]
        )

        result = generate_conversation_research_answer(
            user_id=user_id,
            conversation_id=conversation[
                "conversation_id"
            ],
            question=paper[
                "title"
            ],
            provider=provider,
            top_k=1
        )

        messages = get_ai_conversation_messages(
            user_id,
            conversation[
                "conversation_id"
            ],
            limit=20
        )

        if not result["citation_repair_used"]:
            raise ValueError("FAIL: Conversation result did not record citation repair")

        if messages[-1]["content"] != f"Repaired answer [{paper['paper_id']}].":
            raise ValueError("FAIL: Final repaired answer was not persisted")

        if not messages[-1]["citation_repair_used"]:
            raise ValueError("FAIL: Stored assistant message lost repair metadata")

        print("PASS: Final validated citation-repaired answer is persisted")

    finally:
        delete_user(
            user_id
        )


def test_cross_user_conversation_is_rejected():
    owner_id = create_user()
    other_id = create_user()

    try:
        paper = get_test_paper()

        conversation = create_ai_conversation(
            owner_id
        )

        provider = FakeLLMProvider(
            f"Answer [{paper['paper_id']}]."
        )

        try:
            generate_conversation_research_answer(
                user_id=other_id,
                conversation_id=conversation[
                    "conversation_id"
                ],
                question=paper[
                    "title"
                ],
                provider=provider,
                top_k=1
            )

        except ConversationNotFoundError:
            if provider.calls:
                raise ValueError("FAIL: Provider was called for cross-user conversation")

            print("PASS: Conversation generation enforces authenticated ownership")
            return

        raise ValueError("FAIL: Cross-user conversation generation was allowed")

    finally:
        delete_user(
            owner_id
        )

        delete_user(
            other_id
        )


if __name__ == "__main__":
    setup_ai_conversation_database()

    test_empty_conversation_history()
    test_conversation_history_is_bounded()
    test_prompt_contains_history_and_current_evidence()
    test_prompt_marks_history_as_non_evidence()
    test_generated_exchange_is_persisted()
    test_second_turn_receives_previous_history()
    test_no_evidence_is_stored_without_provider_call()
    test_historical_fake_citation_cannot_become_current_evidence()
    test_repaired_answer_is_persisted()
    test_cross_user_conversation_is_rejected()