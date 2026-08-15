from inspect_research_data import df, validate_research_data, required_columns, required_value_columns


def run_error_test(test_name, test_data, expected_error):
    try:
        validate_research_data(test_data, required_columns, required_value_columns)
        print(f"\n{test_name}: FAIL - validator did not catch the error")

    except ValueError as error:
        if expected_error in str(error):
            print(f"\n{test_name}: PASS")
        else:
            print(f"\n{test_name}: FAIL - wrong error was caught")
            print(error)


def run_valid_test(test_name, test_data):
    try:
        validate_research_data(test_data, required_columns, required_value_columns)
        print(f"\n{test_name}: PASS")

    except ValueError as error:
        print(f"\n{test_name}: FAIL")
        print(error)


# 1. Valid dataset
test_data = df.copy()
run_valid_test("Valid dataset", test_data)


# 2. Invalid paper ID
test_data = df.copy()
test_data.loc[0, "paper_id"] = "BAD001"
run_error_test("Invalid paper ID", test_data, "invalid paper IDs")


# 3. Duplicate paper ID
test_data = df.copy()
test_data.loc[1, "paper_id"] = test_data.loc[0, "paper_id"]
run_error_test("Duplicate paper ID", test_data, "duplicate paper_id")


# 4. Duplicate DOI
test_data = df.copy()
test_data.loc[1, "doi"] = test_data.loc[0, "doi"]
run_error_test("Duplicate DOI", test_data, "duplicate doi")


# 5. Duplicate title with different capitalization and spaces
test_data = df.copy()
test_data.loc[1, "title"] = "   " + test_data.loc[0, "title"].upper() + "   "
run_error_test("Duplicate normalized title", test_data, "duplicate title")


# 6. Invalid DOI format
test_data = df.copy()
test_data.loc[0, "doi"] = "invalid-doi"
run_error_test("Invalid DOI format", test_data, "invalid DOI")


# 7. Non-numeric publication year
test_data = df.copy()
test_data["publication_year"] = test_data["publication_year"].astype("object")
test_data.loc[0, "publication_year"] = "unknown"
run_error_test("Non-numeric publication year", test_data, "invalid publication years")


# 8. Future publication year
test_data = df.copy()
test_data.loc[0, "publication_year"] = 3000
run_error_test("Future publication year", test_data, "invalid publication years")


# 9. Publication year too old
test_data = df.copy()
test_data.loc[0, "publication_year"] = 1800
run_error_test("Publication year too old", test_data, "invalid publication years")


# 10. Invalid source URL
test_data = df.copy()
test_data.loc[0, "source_url"] = "not-a-valid-url"
run_error_test("Invalid source URL", test_data, "invalid URLs in source_url")


# 11. Invalid license URL
test_data = df.copy()
test_data.loc[0, "license_url"] = "not-a-valid-url"
run_error_test("Invalid license URL", test_data, "invalid URLs in license_url")


# 12. Blank required title
test_data = df.copy()
test_data.loc[0, "title"] = "   "
run_error_test("Blank required title", test_data, "missing or blank values")


# 13. Missing required value
test_data = df.copy()
test_data.loc[0, "authors"] = None
run_error_test("Missing required author", test_data, "missing or blank values")


# 14. Missing required column
test_data = df.copy()
test_data = test_data.drop(columns=["title"])
run_error_test("Missing required column", test_data, "Missing required columns")


# 15. Missing DOI is allowed
test_data = df.copy()
test_data.loc[0, "doi"] = None
run_valid_test("Missing optional DOI", test_data)


# 16. Blank DOI is allowed
test_data = df.copy()
test_data.loc[0, "doi"] = ""
run_valid_test("Blank optional DOI", test_data)


# 17. Missing license URL is allowed
test_data = df.copy()
test_data.loc[0, "license_url"] = None
run_valid_test("Missing optional license URL", test_data)