from tfidf_search import search_tfidf

test_queries = [
    ("muscle hypertrophy", ["P001", "P003"]),
    ("training volume for muscle growth", ["P001"]),
    ("strength and repetition ranges", ["P002"]),
    ("advanced resistance training techniques", ["P003"]),
    ("what training variables influence muscle growth", ["P001"]),
    ("what rep range is best for getting stronger", ["P002"]),
    ("heavy loads versus light loads for strength", ["P002"]),
    ("advanced methods for increasing muscle size", ["P003"])
]

for top_k in [1, 2, 3]:
    correct = 0
    total_recall = 0
    total_precision = 0
    total_f1 = 0

    for query, expected in test_queries:
        result = search_tfidf(query, top_n=top_k)

        actual_papers = result["paper_id"].tolist()

        matched_papers = [
            paper for paper in expected
            if paper in actual_papers
        ]

        recall = len(matched_papers) / len(expected)

        if len(actual_papers) > 0:
            precision = len(matched_papers) / len(actual_papers)
        else:
            precision = 0

        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0

        total_f1 += f1

        total_recall += recall
        total_precision += precision

        if any(paper in actual_papers for paper in expected):
            correct += 1
            status = "Pass"
        else:
            status = "Fail"

        print(f"{status} | {query} | expected={expected} | " f"top_{top_k}={actual_papers} | "f"recall={recall:.2%} | precision={precision:.2%} | f1={f1:.2%}")

    hit_rate = correct / len(test_queries)
    average_recall = total_recall / len(test_queries)
    average_precision = total_precision / len(test_queries)
    average_f1 = total_f1 / len(test_queries)

    print(f"\nHit@{top_k}: {hit_rate:.2%}")
    print(f"Mean Recall@{top_k}: {average_recall:.2%}")
    print(f"Mean Precision@{top_k}: {average_precision:.2%}")
    print(f"Mean F1@{top_k}: {average_f1:.2%}\n")