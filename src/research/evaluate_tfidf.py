from tfidf_search import search_tfidf, build_tfidf_index, df, text_columns


indexed_df, vectorizer, tfidf_matrix = build_tfidf_index(df, text_columns)


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
        result = search_tfidf(
            indexed_df,
            vectorizer,
            tfidf_matrix,
            query,
            top_n=top_k
        )

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

        total_recall += recall
        total_precision += precision
        total_f1 += f1

        if any(paper in actual_papers for paper in expected):
            correct += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(
            f"{status} | {query} | expected={expected} | "
            f"top_{top_k}={actual_papers} | "
            f"recall={recall:.2%} | "
            f"precision={precision:.2%} | "
            f"f1={f1:.2%}"
        )

    hit_rate = correct / len(test_queries)
    mean_recall = total_recall / len(test_queries)
    mean_precision = total_precision / len(test_queries)
    mean_f1 = total_f1 / len(test_queries)

    print(f"\nHit@{top_k}: {hit_rate:.2%}")
    print(f"Mean Recall@{top_k}: {mean_recall:.2%}")
    print(f"Mean Precision@{top_k}: {mean_precision:.2%}")
    print(f"Mean F1@{top_k}: {mean_f1:.2%}\n")