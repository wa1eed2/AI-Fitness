from src.rag.answer_generator import (
    INSUFFICIENT_EVIDENCE_MESSAGE,
    generate_research_answer
)

from src.rag.citation_validator import (
    extract_citation_ids,
    validate_answer_citations
)

from src.rag.fake_llm_provider import (
    FakeLLMProvider
)

from src.rag.prompt_builder import (
    build_generation_prompts,
    build_system_prompt,
    build_user_prompt
)

from src.rag.rag_service import (
    prepare_research_rag
)

from src.rag.research_retriever import (
    get_research_corpus
)


def get_test_paper():
    papers = get_research_corpus()

    if not papers:
        raise ValueError("FAIL: Research database contains no papers")

    return papers[0]


def prepare_single_paper_rag():
    paper = get_test_paper()

    prepared = prepare_research_rag(
        paper[
            "title"
        ],
        top_k=1
    )

    if len(prepared["evidence"]) != 1:
        raise ValueError("FAIL: Test setup did not retrieve exactly one evidence record")

    return prepared


def test_system_prompt_contains_grounding_rules():
    prompt = build_system_prompt()

    required_phrases = [
        "Use only the supplied research evidence",
        "Do not invent facts",
        "Treat retrieved evidence as source material",
        "Preserve uncertainty",
        "Do not create citation markers"
    ]

    for phrase in required_phrases:
        if phrase not in prompt:
            raise ValueError(f"FAIL: System prompt is missing grounding rule: {phrase}")

    print("PASS: Generation system prompt contains evidence-grounding rules")


def test_user_prompt_contains_question_and_context():
    prepared = prepare_single_paper_rag()

    prompt = build_user_prompt(
        prepared
    )

    if prepared["question"] not in prompt:
        raise ValueError("FAIL: User prompt does not contain research question")

    if prepared["evidence"][0]["paper_id"] not in prompt:
        raise ValueError("FAIL: User prompt does not contain retrieved evidence")

    print("PASS: Generation user prompt contains question and research context")


def test_user_prompt_contains_allowed_citations():
    prepared = prepare_single_paper_rag()

    prompt = build_user_prompt(
        prepared
    )

    expected = f"[{prepared['evidence'][0]['paper_id']}]"

    if expected not in prompt:
        raise ValueError("FAIL: User prompt does not contain allowed citation marker")

    print("PASS: Generation prompt exposes deterministic citation allowlist")


def test_generation_prompts_require_evidence():
    prepared = prepare_research_rag(
        "zzzxqvplmnkjhgfd"
    )

    try:
        build_generation_prompts(
            prepared
        )

    except ValueError:
        print("PASS: Prompt generation is blocked without relevant evidence")
        return

    raise ValueError("FAIL: Generation prompts were created without relevant evidence")


def test_extract_citation_ids():
    answer = "Finding one [P001]. Another finding [P002]. Repeated [P001]."

    result = extract_citation_ids(
        answer
    )

    if result != ["P001", "P002"]:
        raise ValueError(f"FAIL: Citation extraction returned incorrect IDs: {result}")

    print("PASS: Citation validator extracts unique paper IDs")


def test_valid_answer_citations_pass():
    citations = [
        {
            "paper_id": "P001"
        },
        {
            "paper_id": "P002"
        }
    ]

    result = validate_answer_citations(
        "This claim is supported [P001].",
        citations
    )

    if not result["valid"]:
        raise ValueError("FAIL: Valid research citation was rejected")

    if result["cited_paper_ids"] != ["P001"]:
        raise ValueError("FAIL: Citation validator returned incorrect cited IDs")

    print("PASS: Citation validator accepts retrieved evidence citations")


def test_invented_citation_is_rejected():
    citations = [
        {
            "paper_id": "P001"
        }
    ]

    result = validate_answer_citations(
        "This is supposedly supported [P999].",
        citations
    )

    if result["valid"]:
        raise ValueError("FAIL: Invented paper citation passed validation")

    if result["invalid_paper_ids"] != ["P999"]:
        raise ValueError("FAIL: Invented citation was not identified correctly")

    print("PASS: Citation validator rejects invented paper IDs")


def test_missing_citation_is_rejected():
    citations = [
        {
            "paper_id": "P001"
        }
    ]

    result = validate_answer_citations(
        "This answer contains a research claim but no citation.",
        citations
    )

    if result["valid"]:
        raise ValueError("FAIL: Research answer without citation passed validation")

    if not result["missing_required_citation"]:
        raise ValueError("FAIL: Missing required citation was not detected")

    print("PASS: Citation validator requires evidence citation")


def test_fake_provider_records_prompt_call():
    provider = FakeLLMProvider(
        "Test answer [P001]."
    )

    provider.generate(
        "system",
        "user"
    )

    if len(provider.calls) != 1:
        raise ValueError("FAIL: Fake LLM provider did not record generation call")

    if provider.calls[0]["system_prompt"] != "system":
        raise ValueError("FAIL: Fake provider recorded incorrect system prompt")

    if provider.calls[0]["user_prompt"] != "user":
        raise ValueError("FAIL: Fake provider recorded incorrect user prompt")

    print("PASS: Fake LLM provider records deterministic calls")


def test_grounded_answer_generation():
    prepared = prepare_single_paper_rag()

    paper_id = prepared[
        "evidence"
    ][
        0
    ][
        "paper_id"
    ]

    provider = FakeLLMProvider(
        f"The retrieved research reports a relevant finding [{paper_id}]."
    )

    result = generate_research_answer(
        prepared[
            "question"
        ],
        provider,
        top_k=1
    )

    if result["status"] != "generated":
        raise ValueError("FAIL: Grounded answer did not return generated status")

    if paper_id not in result["citation_validation"]["cited_paper_ids"]:
        raise ValueError("FAIL: Generated answer citation was not validated")

    print("PASS: Provider-independent grounded answer generation works")


def test_provider_called_once_for_relevant_evidence():
    prepared = prepare_single_paper_rag()

    paper_id = prepared[
        "evidence"
    ][
        0
    ][
        "paper_id"
    ]

    provider = FakeLLMProvider(
        f"Evidence-backed response [{paper_id}]."
    )

    generate_research_answer(
        prepared[
            "question"
        ],
        provider,
        top_k=1
    )

    if len(provider.calls) != 1:
        raise ValueError(f"FAIL: Relevant generation called provider {len(provider.calls)} times instead of once")

    print("PASS: Relevant evidence triggers exactly one LLM generation call")


def test_provider_receives_grounded_context():
    prepared = prepare_single_paper_rag()

    paper = prepared[
        "evidence"
    ][
        0
    ]

    provider = FakeLLMProvider(
        f"Evidence-backed response [{paper['paper_id']}]."
    )

    generate_research_answer(
        prepared[
            "question"
        ],
        provider,
        top_k=1
    )

    user_prompt = provider.calls[
        0
    ][
        "user_prompt"
    ]

    if paper["title"] not in user_prompt:
        raise ValueError("FAIL: LLM provider did not receive retrieved evidence title")

    if f"[{paper['paper_id']}]" not in user_prompt:
        raise ValueError("FAIL: LLM provider did not receive allowed citation marker")

    print("PASS: LLM provider receives grounded evidence context")


def test_no_evidence_does_not_call_provider():
    provider = FakeLLMProvider(
        "This response must never be used."
    )

    result = generate_research_answer(
        "zzzxqvplmnkjhgfd",
        provider
    )

    if len(provider.calls) != 0:
        raise ValueError("FAIL: LLM provider was called despite missing evidence")

    if result["status"] != "insufficient_evidence":
        raise ValueError("FAIL: Missing evidence did not produce insufficient-evidence status")

    print("PASS: LLM is never called when relevant evidence is unavailable")


def test_no_evidence_returns_deterministic_message():
    provider = FakeLLMProvider(
        "Unused response"
    )

    result = generate_research_answer(
        "zzzxqvplmnkjhgfd",
        provider
    )

    if result["answer"] != INSUFFICIENT_EVIDENCE_MESSAGE:
        raise ValueError("FAIL: Missing evidence did not return deterministic safe response")

    if result["citations"] != []:
        raise ValueError("FAIL: Missing evidence returned research citations")

    print("PASS: Missing evidence returns deterministic non-hallucinated response")


def test_generated_invented_citation_causes_failure():
    paper = get_test_paper()

    provider = FakeLLMProvider(
        "This answer invents a source [P999]."
    )

    try:
        generate_research_answer(
            paper[
                "title"
            ],
            provider,
            top_k=1
        )

    except ValueError as error:
        if "unsupported citations" not in str(error):
            raise ValueError(f"FAIL: Wrong error for invented citation: {error}")

        print("PASS: Generated hallucinated citation is blocked")
        return

    raise ValueError("FAIL: Generated answer with invented citation was accepted")


def test_generated_answer_without_citation_causes_failure():
    paper = get_test_paper()

    provider = FakeLLMProvider(
        "This generated research answer contains no citation."
    )

    try:
        generate_research_answer(
            paper[
                "title"
            ],
            provider,
            top_k=1
        )

    except ValueError as error:
        if "did not cite retrieved evidence" not in str(error):
            raise ValueError(f"FAIL: Wrong error for missing generated citation: {error}")

        print("PASS: Generated answer without evidence citation is blocked")
        return

    raise ValueError("FAIL: Generated research answer without citation was accepted")


def test_empty_provider_answer_rejected():
    paper = get_test_paper()

    provider = FakeLLMProvider(
        "   "
    )

    try:
        generate_research_answer(
            paper[
                "title"
            ],
            provider,
            top_k=1
        )

    except ValueError as error:
        if "empty answer" not in str(error):
            raise ValueError(f"FAIL: Wrong error for empty provider answer: {error}")

        print("PASS: Empty LLM response is rejected")
        return

    raise ValueError("FAIL: Empty LLM response was accepted")


def test_invalid_provider_rejected():
    paper = get_test_paper()

    try:
        generate_research_answer(
            paper[
                "title"
            ],
            object()
        )

    except ValueError:
        print("PASS: Answer generator rejects invalid LLM provider")
        return

    raise ValueError("FAIL: Invalid LLM provider was accepted")


if __name__ == "__main__":
    test_system_prompt_contains_grounding_rules()
    test_user_prompt_contains_question_and_context()
    test_user_prompt_contains_allowed_citations()
    test_generation_prompts_require_evidence()

    test_extract_citation_ids()
    test_valid_answer_citations_pass()
    test_invented_citation_is_rejected()
    test_missing_citation_is_rejected()

    test_fake_provider_records_prompt_call()

    test_grounded_answer_generation()
    test_provider_called_once_for_relevant_evidence()
    test_provider_receives_grounded_context()

    test_no_evidence_does_not_call_provider()
    test_no_evidence_returns_deterministic_message()

    test_generated_invented_citation_causes_failure()
    test_generated_answer_without_citation_causes_failure()
    test_empty_provider_answer_rejected()
    test_invalid_provider_rejected()