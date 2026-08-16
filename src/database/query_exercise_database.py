import sqlite3
from src.database.setup_exercise_database import db_path

def get_exercise_by_id(exercise_id):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM exercises WHERE exercise_id = ?", (exercise_id,))
    exercise = cursor.fetchone()
    connection.close()

    if exercise is None:
        return None

    return dict(exercise)

def search_exercises(primary_muscle=None, category=None, environment=None, difficulty_level=None, exercise_type=None, movement_pattern=None, body_position=None, equipment=None, difficulty_score=None):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = "SELECT * FROM exercises WHERE 1=1"
    parameters = []

    if primary_muscle:
        query += " AND primary_muscle = ?"
        parameters.append(primary_muscle)

    if category:
        query += " AND category = ?"
        parameters.append(category)

    if environment:
        query += " AND environment = ?"
        parameters.append(environment)

    if difficulty_level:
        query += " AND difficulty_level = ?"
        parameters.append(difficulty_level)

    if exercise_type:
        query += " AND exercise_type = ?"
        parameters.append(exercise_type)

    if movement_pattern:
        query += " AND movement_pattern = ?"
        parameters.append(movement_pattern)

    if body_position:
        query += " AND body_position = ?"
        parameters.append(body_position)

    if equipment:
        query += " AND equipment = ?"
        parameters.append(equipment)

    if difficulty_score is not None:
        query += " AND difficulty_score = ?"
        parameters.append(difficulty_score)


    cursor.execute(query, parameters)
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]

