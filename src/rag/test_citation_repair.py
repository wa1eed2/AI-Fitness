from src.rag.answer_generator import generate_research_answer

from src.rag.citation_repair import (
    build_citation_repair_prompt,
    repair_answer_citations
)

from src.rag.fake_llm_provider import FakeLLMProvider

from src.rag.rag_service import prepare_research_rag

from src.rag.research_retriever import get_research_corpus


class SequentialFakeLLMProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate(self, system_prompt, user_prompt):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            }
        )

        if not self.responses:
            raise ValueError("No fake responses remaining")

        return self.responses.pop(0)


def get_test_paper():
    papers = get_research_corpus()

    if not papers:
        raise ValueError("FAIL: Research database contains no papers")

    return papers[0]


def get_prepared_rag():
    paper = get_test_paper()

    return prepare_research_rag(
        paper["title"],
        top_k=1
    )


def test_repair_prompt_contains_original_answer():
    prepared = get_prepared_rag()

    prompt = build_citation_repair_prompt(
        "Draft answer without citation.",
        prepared
    )

    if "Draft answer without citation." not in prompt:
        raise ValueError("FAIL: Citation repair prompt omitted original answer")

    print("PASS: Citation repair prompt contains draft answer")


def test_repair_prompt_contains_allowed_citation():
    prepared = get_prepared_rag()

    paper_id = prepared[
        "evidence"
    ][
        0
    ][
        "paper_id"
    ]

    prompt = build_citation_repair_prompt(
        "Draft answer.",
        prepared
    )

    if f"[{paper_id}]" not in prompt:
        raise ValueError("FAIL: Citation repair prompt omitted allowed citation")

    print("PASS: Citation repair prompt contains citation allowlist")


def test_repair_prompt_contains_research_context():
    prepared = get_prepared_rag()

    paper = prepared[
        "evidence"
    ][
        0
    ]

    prompt = build_citation_repair_prompt(
        "Draft answer.",
        prepared
    )

    if paper["title"] not in prompt:
        raise ValueError("FAIL: Citation repair prompt omitted research context")

    print("PASS: Citation repair prompt includes research evidence")


def test_repair_provider_is_called():
    prepared = get_prepared_rag()

    paper_id = prepared[
        "evidence"
    ][
        0
    ][
        "paper_id"
    ]

    provider = FakeLLMProvider(
        f"Corrected answer [{paper_id}]."
    )

    result = repair_answer_citations(
        provider=provider,
        answer="Uncited answer.",
        prepared_rag=prepared,
        system_prompt="System"
    )

    if result != f"Corrected answer [{paper_id}].":
        raise ValueError("FAIL: Citation repair returned incorrect answer")

    if len(provider.calls) != 1:
        raise ValueError("FAIL: Citation repair did not call provider exactly once")

    print("PASS: Citation repair calls provider exactly once")


def test_valid_initial_answer_does_not_trigger_repair():
    paper = get_test_paper()

    provider = FakeLLMProvider(
        f"Valid answer [{paper['paper_id']}]."
    )

    result = generate_research_answer(
        paper["title"],
        provider,
        top_k=1
    )

    if len(provider.calls) != 1:
        raise ValueError("FAIL: Valid answer unexpectedly triggered citation repair")

    if result["citation_repair_used"]:
        raise ValueError("FAIL: Valid answer incorrectly reports citation repair")

    print("PASS: Valid initial answer avoids unnecessary repair request")


def test_missing_citation_triggers_single_repair():
    paper = get_test_paper()

    provider = SequentialFakeLLMProvider(
        [
            "Initial answer without citation.",
            f"Corrected answer [{paper['paper_id']}]."
        ]
    )

    result = generate_research_answer(
        paper["title"],
        provider,
        top_k=1
    )

    if len(provider.calls) != 2:
        raise ValueError("FAIL: Missing citation did not trigger exactly one repair request")

    if not result["citation_repair_used"]:
        raise ValueError("FAIL: Result did not report citation repair")

    if not result["citation_validation"]["valid"]:
        raise ValueError("FAIL: Repaired citation was not validated")

    print("PASS: Missing citation triggers one successful repair request")


def test_invented_citation_can_be_repaired():
    paper = get_test_paper()

    provider = SequentialFakeLLMProvider(
        [
            "Initial answer with invented citation [P999].",
            f"Corrected answer [{paper['paper_id']}]."
        ]
    )

    result = generate_research_answer(
        paper["title"],
        provider,
        top_k=1
    )

    if not result["citation_repair_used"]:
        raise ValueError("FAIL: Invented citation did not trigger repair")

    if result["citation_validation"]["invalid_paper_ids"]:
        raise ValueError("FAIL: Repaired answer still contains invalid citation")

    print("PASS: Invented citation can be corrected through bounded repair")


def test_failed_repair_is_rejected():
    paper = get_test_paper()

    provider = SequentialFakeLLMProvider(
        [
            "Initial answer without citation.",
            "Still no citation."
        ]
    )

    try:
        generate_research_answer(
            paper["title"],
            provider,
            top_k=1
        )

    except ValueError as error:
        if "after repair" not in str(error):
            raise ValueError(f"FAIL: Wrong failed-repair error: {error}")

        if len(provider.calls) != 2:
            raise ValueError("FAIL: Failed repair did not stop after one retry")

        print("PASS: Citation repair fails closed after one unsuccessful retry")
        return

    raise ValueError("FAIL: Invalid repaired answer was accepted")


def test_repair_does_not_loop():
    paper = get_test_paper()

    provider = SequentialFakeLLMProvider(
        [
            "No citation.",
            "Still no citation.",
            f"Third response [{paper['paper_id']}]."
        ]
    )

    try:
        generate_research_answer(
            paper["title"],
            provider,
            top_k=1
        )

    except ValueError:
        if len(provider.calls) != 2:
            raise ValueError("FAIL: Citation repair performed more than one retry")

        print("PASS: Citation repair is bounded to one retry")
        return

    raise ValueError("FAIL: Citation repair unexpectedly continued beyond one retry")


if __name__ == "__main__":
    test_repair_prompt_contains_original_answer()
    test_repair_prompt_contains_allowed_citation()
    test_repair_prompt_contains_research_context()
    test_repair_provider_is_called()
    test_valid_initial_answer_does_not_trigger_repair()
    test_missing_citation_triggers_single_repair()
    test_invented_citation_can_be_repaired()
    test_failed_repair_is_rejected()
    test_repair_does_not_loop()