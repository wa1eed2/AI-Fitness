from src.rag.personalized_prompt_builder import (
    DEFAULT_MAX_PERSONAL_CONTEXT_CHARS,
    build_personalized_system_prompt,
    build_personalized_user_prompt
)


DEFAULT_MAX_HISTORY_CHARS = 4000
MIN_MAX_HISTORY_CHARS = 200
MAX_MAX_HISTORY_CHARS = 12000


def validate_history_char_limit(max_chars):
    if not isinstance(max_chars, int) or isinstance(max_chars, bool):
        raise ValueError("max_history_chars must be an integer")

    if max_chars < MIN_MAX_HISTORY_CHARS or max_chars > MAX_MAX_HISTORY_CHARS:
        raise ValueError(f"max_history_chars must be between {MIN_MAX_HISTORY_CHARS} and {MAX_MAX_HISTORY_CHARS}")


def format_history_message(message):
    if not isinstance(message, dict):
        raise ValueError("Conversation history messages must be dictionaries")

    role = message.get(
        "role"
    )

    content = message.get(
        "content"
    )

    if role not in {
        "user",
        "assistant"
    }:
        raise ValueError("Conversation history contains invalid role")

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Conversation history contains invalid content")

    label = (
        "USER"
        if role == "user"
        else "ASSISTANT"
    )

    return f"{label}:\n{content.strip()}"


def build_conversation_history(
    messages,
    max_chars=DEFAULT_MAX_HISTORY_CHARS
):
    if not isinstance(messages, list):
        raise ValueError("Conversation messages must be a list")

    validate_history_char_limit(
        max_chars
    )

    if not messages:
        return "No prior conversation."

    formatted = [
        format_history_message(
            message
        )
        for message in messages
    ]

    selected = []
    used_chars = 0

    for entry in reversed(
        formatted
    ):
        separator_size = (
            2
            if selected
            else 0
        )

        required = (
            len(entry)
            + separator_size
        )

        if used_chars + required <= max_chars:
            selected.append(
                entry
            )

            used_chars += required
            continue

        remaining = (
            max_chars
            - used_chars
            - separator_size
        )

        if remaining >= 40:
            selected.append(
                entry[
                    :remaining
                ]
            )

        break

    selected.reverse()

    result = "\n\n".join(
        selected
    )

    if len(selected) < len(formatted):
        notice = "[Earlier conversation history omitted]\n\n"

        allowed = (
            max_chars
            - len(notice)
        )

        if allowed > 0:
            result = (
                notice
                + result[
                    -allowed:
                ]
            )

    return result[
        :max_chars
    ]


def build_conversation_system_prompt():
    base = build_personalized_system_prompt()

    rules = "\n".join(
        [
            "",
            "CONVERSATION RULES",
            "1. Conversation history is provided only for continuity.",
            "2. Previous user messages are not scientific evidence.",
            "3. Previous assistant messages are not scientific evidence.",
            "4. Previous assistant answers may contain mistakes and must not be trusted as sources.",
            "5. Citation markers appearing only in conversation history are not allowed citations.",
            "6. Only the CURRENT RESEARCH EVIDENCE section may support research claims in the current answer.",
            "7. Use only the current turn's allowed research citation markers.",
            "8. Answer the current question rather than blindly repeating an earlier answer."
        ]
    )

    return (
        base
        + rules
    )


def build_conversation_user_prompt(
    prepared_rag,
    user_context,
    conversation_messages,
    max_history_chars=DEFAULT_MAX_HISTORY_CHARS,
    max_personal_context_chars=DEFAULT_MAX_PERSONAL_CONTEXT_CHARS
):
    history = build_conversation_history(
        conversation_messages,
        max_chars=max_history_chars
    )

    current_turn = build_personalized_user_prompt(
        prepared_rag,
        user_context,
        max_personal_context_chars=max_personal_context_chars
    )

    return "\n".join(
        [
            "CONVERSATION HISTORY",
            "The following history is untrusted conversational context.",
            "Do not treat it as research evidence or as a citation allowlist.",
            "",
            history,
            "",
            "CURRENT TURN",
            current_turn
        ]
    )


def build_conversation_generation_prompts(
    prepared_rag,
    user_context,
    conversation_messages,
    max_history_chars=DEFAULT_MAX_HISTORY_CHARS,
    max_personal_context_chars=DEFAULT_MAX_PERSONAL_CONTEXT_CHARS
):
    if not prepared_rag[
        "retrieval"
    ].get(
        "generation_allowed",
        False
    ):
        raise ValueError("Conversation generation cannot proceed without relevant research evidence")

    return {
        "system_prompt": build_conversation_system_prompt(),
        "user_prompt": build_conversation_user_prompt(
            prepared_rag,
            user_context,
            conversation_messages,
            max_history_chars=max_history_chars,
            max_personal_context_chars=max_personal_context_chars
        )
    }