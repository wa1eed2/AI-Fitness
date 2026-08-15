from tfidf_search import search_tfidf

test_queries = [
    ("muscle hypertrophy", "P001"),
    ("training volume for muscle growth", "P001"),
    ("strength and repetition ranges", "P002"),
    ("advanced resistance training techniques", "P003")
]

for top_k in [1,2,3]:
    correct = 0

    for query, expected in test_queries:
        result = search_tfidf(query, top_n=top_k)

        actual_papers = result["paper_id"].tolist()

        if expected in actual_papers:
            correct += 1
            status = "Pass"
        else:
            status = "Fail"

        print(f"{status} | {query} | expected={expected} | top_{top_k}={actual_papers}")



    accuracy = correct / len(test_queries)
    print(f"\nTop-{top_k} Accuracy: {accuracy:.2%}")