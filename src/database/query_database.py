import sqlite3

db_path = r"C:\Users\HP\PycharmProjects\AI-Fitness\data\database\ai_fitness.db"


def search_research_db(keyword=None, topic=None, subtopic=None, min_year=None, max_year=None, study_design=None, limit=None):
    if min_year is not None and max_year is not None and min_year > max_year:
        raise ValueError("min_year cannot be greater than max_year")

    if limit is not None and limit < 1:
        raise ValueError("Limit must be at least 1.")

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = "SELECT paper_id, title, publication_year FROM research_papers WHERE 1=1"
    parameters = []

    if keyword:
        query += " AND (title LIKE ? OR authors LIKE ? OR study_design LIKE ? OR research_topic LIKE ? OR subtopic LIKE ? OR results_summary LIKE ?)"
        keyword_value = f"%{keyword}%"
        parameters.extend([keyword_value, keyword_value, keyword_value, keyword_value, keyword_value, keyword_value])

    if topic:
        query += " AND research_topic = ?"
        parameters.append(topic)

    if subtopic:
        query += " AND subtopic LIKE ?"
        parameters.append(f"%{subtopic}%")

    if min_year is not None:
        query += " AND publication_year >= ?"
        parameters.append(min_year)

    if max_year is not None:
        query += " AND publication_year <= ?"
        parameters.append(max_year)

    if study_design:
        query += " AND study_design = ?"
        parameters.append(study_design)

    query += " ORDER BY publication_year ASC"

    if limit is not None:
        query += " LIMIT ?"
        parameters.append(limit)

    cursor.execute(query, parameters)

    rows = cursor.fetchall()
    results = [dict(row) for row in rows]

    connection.close()
    return results


def get_paper_by_id(paper_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM research_papers WHERE paper_id = ?", (paper_id,))
    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def count_research_papers():
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM research_papers")
    count = cursor.fetchone()[0]

    connection.close()
    return count


def get_research_topics():
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("SELECT DISTINCT research_topic FROM research_papers ORDER BY research_topic ASC")
    rows = cursor.fetchall()

    connection.close()
    return [row[0] for row in rows]


def count_papers_by_topic():
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("SELECT research_topic, COUNT(*) FROM research_papers GROUP BY research_topic ORDER BY research_topic ASC")
    rows = cursor.fetchall()

    connection.close()
    return rows



if __name__ == "__main__":
    results = search_research_db(topic="Training", limit=2)

    for row in results:
        print(row)

    paper = get_paper_by_id("P999")
    print(paper)

    print("Number of research papers:", count_research_papers())

    topics = get_research_topics()
    print(topics)

    topic_counts = count_papers_by_topic()

    for topic, count in topic_counts:
        print(topic, count)