from src.database.setup_database import sync_research_database
from src.database.query_database import count_research_papers, get_paper_by_id, search_research_db

sync_research_database()

count = count_research_papers()

if count > 0:
    print(f"PASS: Database contains {count} research papers")
else:
    raise ValueError("FAIL: Research database is empty")

paper = get_paper_by_id("P001")
if paper is not None and paper["paper_id"]=="P001":
    print("PASS: Existing paper retrieved successfully")
else:
    raise ValueError("FAIL: Existing paper could not be retrieved")

paper = get_paper_by_id("P999")

if paper is None:
    print("PASS: Missing paper returns None")
else:
    raise ValueError("FAIL: Missing paper returns None")

result = search_research_db(topic="Training", limit=2)

if len(result) == 2:
    print("PASS: Search limit returned 2 papers")
else:
    raise ValueError("FAIL: Search limit did not return 2 papers")

try:
    search_research_db(min_year=2025, max_year=2020)
    raise ValueError("FAIL: Invalid year range was not rejected")

except ValueError as error:

    if str(error) == "min_year cannot be greater than max_year":
        print("PASS: Invalid year range was rejected")
    else:
        raise

result = search_research_db(keyword="hypertrophy")

if len(result) > 0:
    print("PASS: Keyword search returned result")
else:
    raise ValueError("FAIL: Keyword search returned no result")

keyword_found = any("hypertrophy" in row["title"].casefold() for row in result)
if keyword_found:
    print("PASS: Keyword found in returned titles")
else:
    raise ValueError("FAIL: Keyword not found in returned titles")

try:
    search_research_db(limit=0)
    raise ValueError("FAIL: Invalid limit was not rejected")

except ValueError as error:
    if str(error) == "Limit must be at least 1.":
        print("PASS: Invalid limit was rejected")
    else:
        raise