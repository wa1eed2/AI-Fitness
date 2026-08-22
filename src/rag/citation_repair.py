from src.rag.prompt_builder import get_allowed_citation_ids


def validate_repair_inputs(answer, prepared_rag):
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Answer to repair must be a non-empty string")

    if not isinstance(prepared_rag, dict):
        raise ValueError("Prepared RAG data must be a dictionary")

    if "citations" not in prepared_rag:
        raise ValueError("Prepared RAG data requires citations")

    if "context" not in prepared_rag:
        raise ValueError("Prepared RAG data requires research context")


def build_citation_repair_prompt(answer, prepared_rag):
    validate_repair_inputs(answer, prepared_rag)

    allowed_citations = get_allowed_citation_ids(
        prepared_rag["citations"]
    )

    if not allowed_citations:
        raise ValueError("Citation repair requires at least one allowed citation")

    allowed_text = ", ".join(allowed_citations)

    return "\n".join(
        [
            "CITATION REPAIR TASK",
            "",
            "Rewrite the draft answer so that every research-supported claim is grounded in the supplied evidence.",
            "Preserve the useful meaning of the answer but remove anything that is not supported by the evidence.",
            "",
            "STRICT RULES",
            "1. Use only the supplied research evidence.",
            "2. Do not invent new facts, statistics, studies, or conclusions.",
            "3. Use only citation markers from the allowed list.",
            "4. Include at least one exact allowed citation marker.",
            "5. Put citation markers immediately after the claims they support.",
            "6. Do not mention this repair task in the final answer.",
            "",
            "ALLOWED CITATIONS",
            allowed_text,
            "",
            "RESEARCH EVIDENCE",
            prepared_rag["context"],
            "",
            "DRAFT ANSWER",
            answer.strip(),
            "",
            "Return only the corrected final answer."
        ]
    )


def repair_answer_citations(provider, answer, prepared_rag, system_prompt):
    if provider is None:
        raise ValueError("LLM provider is required")

    repair_prompt = build_citation_repair_prompt(
        answer,
        prepared_rag
    )

    repaired_answer = provider.generate(
        system_prompt,
        repair_prompt
    )

    if not isinstance(repaired_answer, str):
        raise ValueError("LLM provider must return a string")

    repaired_answer = repaired_answer.strip()

    if not repaired_answer:
        raise ValueError("LLM provider returned an empty citation-repair answer")

    return repaired_answer