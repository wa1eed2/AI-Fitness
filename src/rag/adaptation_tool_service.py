from src.database.query_adaptation_database import (
    create_adaptation_proposal
)

from src.database.query_ai_conversation_database import (
    add_ai_conversation_exchange,
    get_ai_conversation
)

from src.personalization.adaptation_engine import (
    ACTION_INSUFFICIENT_DATA,
    ACTION_MAINTAIN,
    ACTION_PROGRESS_CAUTIOUSLY,
    ACTION_REDUCE_VOLUME,
    evaluate_training_adaptation
)

from src.rag.adaptation_prompt_builder import (
    DEFAULT_MAX_ADAPTATION_DATA_CHARS,
    build_adaptation_prompts,
    validate_adaptation_evaluation
)

from src.rag.citation_validator import (
    extract_citation_ids
)

from src.rag.conversation_service import (
    ConversationNotFoundError
)

from src.rag.llm_provider import (
    LLMProviderUnavailableError
)


VALID_ADAPTATION_ACTIONS = {
    ACTION_INSUFFICIENT_DATA,
    ACTION_MAINTAIN,
    ACTION_PROGRESS_CAUTIOUSLY,
    ACTION_REDUCE_VOLUME
}


def normalize_adaptation_question(
    question
):
    if not isinstance(question, str):
        raise ValueError("Question must be a string")

    normalized = " ".join(
        question.strip().split()
    )

    if not normalized:
        raise ValueError("Question cannot be empty")

    return normalized


def validate_adaptation_provider(
    provider
):
    if provider is None:
        raise ValueError("LLM provider is required")

    generate = getattr(
        provider,
        "generate",
        None
    )

    if not callable(generate):
        raise ValueError("LLM provider must implement generate")

    return provider


def validate_adaptation_explanation(
    answer
):
    if not isinstance(answer, str):
        raise ValueError("Generated adaptation explanation must be a string")

    normalized = answer.strip()

    if not normalized:
        raise ValueError("Generated adaptation explanation cannot be empty")

    citation_ids = extract_citation_ids(
        normalized
    )

    if citation_ids:
        raise ValueError(
            f"Adaptation explanation invented research citations: {citation_ids}"
        )

    return normalized


def validate_created_proposal(
    proposal,
    expected_action
):
    if not isinstance(proposal, dict):
        raise ValueError("Adaptation proposal creator returned invalid result")

    proposal_id = proposal.get(
        "proposal_id"
    )

    if not isinstance(proposal_id, int) or isinstance(proposal_id, bool) or proposal_id < 1:
        raise ValueError("Adaptation proposal creator returned invalid proposal_id")

    if proposal.get("action") != expected_action:
        raise ValueError("Stored adaptation proposal action does not match evaluation")

    if proposal.get("status") != "pending":
        raise ValueError("New adaptation proposal must be pending")

    return proposal


def build_deterministic_adaptation_explanation(
    evaluation,
    proposal
):
    action = evaluation[
        "action"
    ]

    proposal_id = proposal[
        "proposal_id"
    ]

    reason_codes = evaluation.get(
        "reason_codes",
        []
    )

    if action == ACTION_INSUFFICIENT_DATA:
        reasons = ", ".join(
            reason_codes
        )

        if not reasons:
            reasons = "insufficient reliable training data"

        return (
            "There is not enough reliable training information to recommend a "
            f"change yet. The deterministic evaluator recorded: {reasons}. "
            f"Adaptation record {proposal_id} is pending for review. "
            "No training setting has been changed."
        )

    if action == ACTION_MAINTAIN:
        return (
            "The deterministic evaluator recommends maintaining the current "
            "training approach. The available signals do not meet the guarded "
            "criteria for progression or volume reduction. "
            f"Adaptation record {proposal_id} is pending for review. "
            "No training setting has been changed."
        )

    if action == ACTION_PROGRESS_CAUTIOUSLY:
        return (
            "The deterministic evaluator supports a cautious progression proposal "
            "based on the recorded training, progression, logging-quality, and "
            "exertion signals. This is only a proposal. "
            f"Proposal {proposal_id} must be accepted and then explicitly applied "
            "through the adaptation workflow before anything changes."
        )

    if action == ACTION_REDUCE_VOLUME:
        return (
            "The deterministic evaluator produced a training-volume reduction "
            "proposal because the recorded training data contained both the "
            "required high-exertion pattern and declining progression signal. "
            "This is a training-data signal, not a medical diagnosis. "
            f"Proposal {proposal_id} must be accepted and then explicitly applied "
            "before anything changes."
        )

    raise ValueError("Unsupported adaptation action")


def build_authoritative_adaptation_answer(
    evaluation,
    proposal,
    explanation
):
    action = evaluation[
        "action"
    ]

    normalized_explanation = validate_adaptation_explanation(
        explanation
    )

    return (
        f"Deterministic adaptation result: {action}. "
        "No training change has been applied.\n\n"
        f"{normalized_explanation}"
    )


def persist_adaptation_exchange(
    user_id,
    conversation_id,
    question,
    answer,
    action,
    explanation_source
):
    retrieval_status = (
        f"adaptation:{action}"
    )

    if explanation_source == "deterministic_fallback":
        retrieval_status += ":provider_fallback"

    elif explanation_source == "deterministic":
        retrieval_status += ":deterministic"

    exchange = add_ai_conversation_exchange(
        user_id=user_id,
        conversation_id=conversation_id,
        user_content=question,
        assistant_content=answer,
        citations=[],
        retrieval_status=retrieval_status,
        citation_repair_used=False
    )

    if exchange is None:
        raise ConversationNotFoundError("Conversation was not found")

    return exchange


def generate_adaptation_conversation_answer(
    user_id,
    conversation_id,
    question,
    provider,
    reference_date=None,
    max_adaptation_data_chars=DEFAULT_MAX_ADAPTATION_DATA_CHARS,
    evaluator=None,
    proposal_creator=None
):
    normalized_question = normalize_adaptation_question(
        question
    )

    conversation = get_ai_conversation(
        user_id,
        conversation_id
    )

    if conversation is None:
        raise ConversationNotFoundError("Conversation was not found")

    if evaluator is None:
        evaluator = evaluate_training_adaptation

    if proposal_creator is None:
        proposal_creator = create_adaptation_proposal

    if not callable(evaluator):
        raise ValueError("evaluator must be callable")

    if not callable(proposal_creator):
        raise ValueError("proposal_creator must be callable")

    evaluation = evaluator(
        user_id,
        reference_date=reference_date
    )

    validate_adaptation_evaluation(
        evaluation
    )

    action = evaluation[
        "action"
    ]

    if action not in VALID_ADAPTATION_ACTIONS:
        raise ValueError("Adaptation evaluator returned unsupported action")

    proposal = proposal_creator(
        user_id,
        evaluation
    )

    validate_created_proposal(
        proposal,
        action
    )

    provider_available = None
    explanation_source = "deterministic"

    if action == ACTION_INSUFFICIENT_DATA:
        explanation = build_deterministic_adaptation_explanation(
            evaluation,
            proposal
        )

    else:
        validate_adaptation_provider(
            provider
        )

        prompts = build_adaptation_prompts(
            question=normalized_question,
            evaluation=evaluation,
            proposal=proposal,
            max_adaptation_data_chars=max_adaptation_data_chars
        )

        try:
            generated_explanation = provider.generate(
                prompts[
                    "system_prompt"
                ],
                prompts[
                    "user_prompt"
                ]
            )

            explanation = validate_adaptation_explanation(
                generated_explanation
            )

            provider_available = True
            explanation_source = "llm"

        except LLMProviderUnavailableError:
            explanation = build_deterministic_adaptation_explanation(
                evaluation,
                proposal
            )

            provider_available = False
            explanation_source = "deterministic_fallback"

    answer = build_authoritative_adaptation_answer(
        evaluation,
        proposal,
        explanation
    )

    exchange = persist_adaptation_exchange(
        user_id=user_id,
        conversation_id=conversation_id,
        question=normalized_question,
        answer=answer,
        action=action,
        explanation_source=explanation_source
    )

    return {
        "status": "adaptation_evaluated",
        "conversation_id": conversation_id,
        "route": "adaptation",
        "question": normalized_question,
        "action": action,
        "answer": answer,
        "evaluation": evaluation,
        "proposal": proposal,
        "applied": False,
        "provider_available": provider_available,
        "explanation_source": explanation_source,
        "citations": [],
        "citation_validation": {
            "valid": True,
            "cited_paper_ids": [],
            "allowed_paper_ids": [],
            "invalid_paper_ids": [],
            "uncited_evidence_ids": [],
            "missing_required_citation": False
        },
        "citation_repair_used": False,
        "user_message": exchange[
            "user_message"
        ],
        "assistant_message": exchange[
            "assistant_message"
        ]
    }