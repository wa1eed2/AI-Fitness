def clean_citation_value(
    value
):
    if value is None:
        return None

    text = str(
        value
    ).strip()

    if not text:
        return None

    return text


def build_citation(
    paper
):
    if not isinstance(paper, dict):
        raise ValueError("Paper must be a dictionary")

    paper_id = clean_citation_value(
        paper.get(
            "paper_id"
        )
    )

    title = clean_citation_value(
        paper.get(
            "title"
        )
    )

    if paper_id is None:
        raise ValueError("Paper citation requires paper_id")

    if title is None:
        raise ValueError("Paper citation requires title")

    authors = clean_citation_value(
        paper.get(
            "authors"
        )
    )

    publication_year = clean_citation_value(
        paper.get(
            "publication_year"
        )
    )

    journal = clean_citation_value(
        paper.get(
            "journal"
        )
    )

    display_parts = []

    if authors:
        display_parts.append(
            authors
        )

    if publication_year:
        display_parts.append(
            f"({publication_year})"
        )

    display_parts.append(
        title
    )

    if journal:
        display_parts.append(
            journal
        )

    display = ". ".join(
        display_parts
    )

    if not display.endswith(
        "."
    ):
        display += "."

    return {
        "citation_id": f"[{paper_id}]",
        "paper_id": paper_id,
        "title": title,
        "authors": authors,
        "publication_year": publication_year,
        "journal": journal,
        "doi": clean_citation_value(
            paper.get(
                "doi"
            )
        ),
        "source_url": clean_citation_value(
            paper.get(
                "source_url"
            )
        ),
        "license": clean_citation_value(
            paper.get(
                "license"
            )
        ),
        "license_url": clean_citation_value(
            paper.get(
                "license_url"
            )
        ),
        "similarity_score": paper.get(
            "similarity_score"
        ),
        "display": display
    }


def build_citations(
    papers
):
    if not isinstance(papers, list):
        raise ValueError("Papers must be provided as a list")

    citations = []
    seen_paper_ids = set()

    for paper in papers:
        citation = build_citation(
            paper
        )

        paper_id = citation[
            "paper_id"
        ]

        if paper_id in seen_paper_ids:
            continue

        seen_paper_ids.add(
            paper_id
        )

        citations.append(
            citation
        )

    return citations