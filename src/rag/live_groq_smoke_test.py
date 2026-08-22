import os

from src.rag.answer_generator import generate_research_answer

from src.rag.groq_provider import GroqProvider

from src.rag.research_retriever import get_research_corpus


def require_live_configuration():
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY is not configured")

    print("LIVE TEST: Groq API configuration detected")


def get_smoke_test_paper():
    papers = get_research_corpus()

    if not papers:
        raise ValueError("Research database contains no papers")

    return papers[0]


def run_live_smoke_test():
    require_live_configuration()

    paper = get_smoke_test_paper()

    provider = GroqProvider()

    print(f"LIVE TEST PROVIDER: Groq")
    print(f"LIVE TEST MODEL: {provider.model}")
    print(f"LIVE TEST MAX OUTPUT TOKENS: {provider.max_output_tokens}")
    print(f"LIVE TEST PAPER: {paper['paper_id']} - {paper['title']}")
    print("LIVE TEST: Sending one evidence-grounded request...")

    result = generate_research_answer(
        question=paper["title"],
        provider=provider,
        top_k=1,
        min_relevance_score=0.05,
        strong_relevance_score=0.20,
        max_context_chars=4000
    )

    if result["status"] != "generated":
        raise ValueError(f"LIVE TEST FAILED: Unexpected result status: {result['status']}")

    if not result["citation_validation"]["valid"]:
        raise ValueError("LIVE TEST FAILED: Generated citations did not pass validation")

    if paper["paper_id"] not in result["citation_validation"]["cited_paper_ids"]:
        raise ValueError("LIVE TEST FAILED: Expected research paper was not cited")

    print("LIVE TEST PASS: Groq produced a citation-validated RAG answer")
    print()
    print("ANSWER")
    print("------")
    print(result["answer"])
    print()
    print("VALIDATED CITATIONS")
    print("-------------------")

    for citation in result["citations"]:
        print(f"{citation['citation_id']} {citation.get('title', '')}")


if __name__ == "__main__":
    run_live_smoke_test()