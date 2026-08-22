import re


PAPER_CITATION_PATTERN = re.compile(
    r"\[([Pp]\d+)\]"
)


def extract_citation_ids(
    answer
):
    if not isinstance(answer, str):
        raise ValueError("Answer must be a string")

    matches = PAPER_CITATION_PATTERN.findall(
        answer
    )

    citation_ids = []

    for match in matches:
        normalized = match.upper()

        if normalized not in citation_ids:
            citation_ids.append(
                normalized
            )

    return citation_ids


def get_allowed_paper_ids(
    citations
):
    if not isinstance(citations, list):
        raise ValueError("Citations must be provided as a list")

    allowed = []

    for citation in citations:
        if not isinstance(citation, dict):
            raise ValueError("Each citation must be a dictionary")

        paper_id = citation.get(
            "paper_id"
        )

        if paper_id is None:
            continue

        normalized = str(
            paper_id
        ).strip().upper()

        if normalized and normalized not in allowed:
            allowed.append(
                normalized
            )

    return allowed


def validate_answer_citations(
    answer,
    citations,
    require_citation=True
):
    if not isinstance(answer, str):
        raise ValueError("Answer must be a string")

    if not answer.strip():
        raise ValueError("Answer cannot be empty")

    if not isinstance(require_citation, bool):
        raise ValueError("require_citation must be a boolean")

    cited_paper_ids = extract_citation_ids(
        answer
    )

    allowed_paper_ids = get_allowed_paper_ids(
        citations
    )

    invalid_paper_ids = [
        paper_id
        for paper_id in cited_paper_ids
        if paper_id not in allowed_paper_ids
    ]

    missing_required_citation = (
        require_citation
        and bool(
            allowed_paper_ids
        )
        and not bool(
            cited_paper_ids
        )
    )

    valid = (
        not invalid_paper_ids
        and not missing_required_citation
    )

    uncited_evidence_ids = [
        paper_id
        for paper_id in allowed_paper_ids
        if paper_id not in cited_paper_ids
    ]

    return {
        "valid": valid,
        "cited_paper_ids": cited_paper_ids,
        "allowed_paper_ids": allowed_paper_ids,
        "invalid_paper_ids": invalid_paper_ids,
        "uncited_evidence_ids": uncited_evidence_ids,
        "missing_required_citation": missing_required_citation
    }