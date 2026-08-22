import json


VALID_ADAPTATION_ACTIONS = {
    "insufficient_data",
    "maintain",
    "progress_cautiously",
    "reduce_volume"
}


DEFAULT_MAX_ADAPTATION_DATA_CHARS = 8000
MIN_ADAPTATION_DATA_CHARS = 1000
MAX_ADAPTATION_DATA_CHARS = 20000


def validate_question(question):
    if not isinstance(question, str):
        raise ValueError("Question must be a string")

    normalized = " ".join(
        question.strip().split()
    )

    if not normalized:
        raise ValueError("Question cannot be empty")

    return normalized


def validate_max_adaptation_data_chars(
    max_adaptation_data_chars
):
    if not isinstance(max_adaptation_data_chars, int) or isinstance(max_adaptation_data_chars, bool):
        raise ValueError("max_adaptation_data_chars must be an integer")

    if (
        max_adaptation_data_chars
        < MIN_ADAPTATION_DATA_CHARS
        or max_adaptation_data_chars
        > MAX_ADAPTATION_DATA_CHARS
    ):
        raise ValueError(
            "max_adaptation_data_chars must be between "
            f"{MIN_ADAPTATION_DATA_CHARS} and {MAX_ADAPTATION_DATA_CHARS}"
        )

    return max_adaptation_data_chars


def validate_adaptation_evaluation(
    evaluation
):
    if not isinstance(evaluation, dict):
        raise ValueError("Adaptation evaluation must be a dictionary")

    action = evaluation.get(
        "action"
    )

    if action not in VALID_ADAPTATION_ACTIONS:
        raise ValueError("Adaptation evaluation contains invalid action")

    reason_codes = evaluation.get(
        "reason_codes"
    )

    signals = evaluation.get(
        "signals"
    )

    recommendation = evaluation.get(
        "recommendation"
    )

    if not isinstance(reason_codes, list):
        raise ValueError("Adaptation evaluation requires reason_codes list")

    if not isinstance(signals, dict):
        raise ValueError("Adaptation evaluation requires signals dictionary")

    if not isinstance(recommendation, dict):
        raise ValueError("Adaptation evaluation requires recommendation dictionary")

    return evaluation


def validate_adaptation_proposal(
    proposal
):
    if not isinstance(proposal, dict):
        raise ValueError("Adaptation proposal must be a dictionary")

    proposal_id = proposal.get(
        "proposal_id"
    )

    if not isinstance(proposal_id, int) or isinstance(proposal_id, bool) or proposal_id < 1:
        raise ValueError("Adaptation proposal requires positive proposal_id")

    if proposal.get("action") not in VALID_ADAPTATION_ACTIONS:
        raise ValueError("Adaptation proposal contains invalid action")

    if proposal.get("status") not in {
        "pending",
        "accepted",
        "rejected"
    }:
        raise ValueError("Adaptation proposal contains invalid status")

    return proposal


def build_adaptation_prompt_payload(
    evaluation,
    proposal
):
    validate_adaptation_evaluation(
        evaluation
    )

    validate_adaptation_proposal(
        proposal
    )

    return {
        "deterministic_evaluation": {
            "action": evaluation[
                "action"
            ],
            "reason_codes": evaluation[
                "reason_codes"
            ],
            "signals": evaluation[
                "signals"
            ],
            "recommendation": evaluation[
                "recommendation"
            ]
        },
        "proposal": {
            "proposal_id": proposal[
                "proposal_id"
            ],
            "action": proposal[
                "action"
            ],
            "status": proposal[
                "status"
            ],
            "created_at": proposal.get(
                "created_at"
            )
        }
    }


def serialize_adaptation_prompt_payload(
    evaluation,
    proposal,
    max_adaptation_data_chars=DEFAULT_MAX_ADAPTATION_DATA_CHARS
):
    validate_max_adaptation_data_chars(
        max_adaptation_data_chars
    )

    payload = build_adaptation_prompt_payload(
        evaluation,
        proposal
    )

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        default=str
    )

    if len(serialized) > max_adaptation_data_chars:
        raise ValueError("Adaptation data exceeds prompt safety limit")

    return serialized


def build_adaptation_prompts(
    question,
    evaluation,
    proposal,
    max_adaptation_data_chars=DEFAULT_MAX_ADAPTATION_DATA_CHARS
):
    normalized_question = validate_question(
        question
    )

    serialized_data = serialize_adaptation_prompt_payload(
        evaluation,
        proposal,
        max_adaptation_data_chars=max_adaptation_data_chars
    )

    system_prompt = (
        "You are the explanation layer for a deterministic fitness adaptation system.\n"
        "\n"
        "The Python adaptation result provided to you is authoritative.\n"
        "You do not decide the adaptation action.\n"
        "You do not change the adaptation action.\n"
        "You do not change any metric, threshold, reason code, or stored value.\n"
        "You do not accept, apply, reject, or roll back adaptation proposals.\n"
        "You do not modify the user's profile, workout plan, nutrition, or settings.\n"
        "\n"
        "Your only job is to explain why the deterministic result was reached in "
        "clear fitness-coaching language.\n"
        "\n"
        "Do not propose a different action.\n"
        "Do not invent exact percentages, minutes, sets, repetitions, weights, "
        "training days, calories, or other modifications.\n"
        "Do not claim that any training change has already been applied.\n"
        "Do not diagnose overtraining, injury, illness, fatigue disorders, or any "
        "medical condition.\n"
        "RPE and RIR values are training-exertion observations, not diagnoses.\n"
        "\n"
        "This route contains no scientific research evidence.\n"
        "Do not create research citations.\n"
        "Do not create citation markers such as [P001].\n"
        "\n"
        "If the action is progress_cautiously or reduce_volume, explain that the "
        "result is only a proposal and requires separate user acceptance and "
        "explicit application before anything changes.\n"
        "\n"
        "If the action is maintain, explain why the current approach should remain "
        "unchanged based only on the supplied deterministic signals.\n"
        "\n"
        "If the action is insufficient_data, explain what category of data is "
        "missing or insufficient without inventing missing measurements."
    )

    user_prompt = (
        "User question:\n"
        f"{normalized_question}\n"
        "\n"
        "Authoritative deterministic adaptation data:\n"
        f"{serialized_data}\n"
        "\n"
        "Explain the deterministic result. Do not replace it with your own decision."
    )

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt
    }