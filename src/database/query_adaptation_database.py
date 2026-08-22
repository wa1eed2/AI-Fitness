import json

from src.database.query_workout_log_database import (
    get_connection
)

from src.database.setup_adaptation_database import (
    setup_adaptation_database
)


VALID_ACTIONS = {
    "insufficient_data",
    "maintain",
    "progress_cautiously",
    "reduce_volume"
}


VALID_RESOLUTION_STATUSES = {
    "accepted",
    "rejected"
}


def validate_positive_integer(value, field_name):
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


def validate_limit(limit):
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("limit must be an integer")

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")


def validate_evaluation(evaluation):
    if not isinstance(evaluation, dict):
        raise ValueError("evaluation must be a dictionary")

    action = evaluation.get(
        "action"
    )

    if action not in VALID_ACTIONS:
        raise ValueError("evaluation contains invalid adaptation action")

    reason_codes = evaluation.get(
        "reason_codes"
    )

    signals = evaluation.get(
        "signals"
    )

    recommendation = evaluation.get(
        "recommendation"
    )

    if not isinstance(reason_codes, list):
        raise ValueError("evaluation reason_codes must be a list")

    if not isinstance(signals, dict):
        raise ValueError("evaluation signals must be a dictionary")

    if not isinstance(recommendation, dict):
        raise ValueError("evaluation recommendation must be a dictionary")

    return evaluation


def serialize_json(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True
    )


def deserialize_json(value):
    if value is None:
        return None

    return json.loads(
        value
    )


def row_to_adaptation_proposal(row):
    if row is None:
        return None

    return {
        "proposal_id": row[
            "proposal_id"
        ],
        "user_id": row[
            "user_id"
        ],
        "action": row[
            "action"
        ],
        "status": row[
            "status"
        ],
        "reason_codes": deserialize_json(
            row[
                "reason_codes_json"
            ]
        ),
        "signals": deserialize_json(
            row[
                "signals_json"
            ]
        ),
        "recommendation": deserialize_json(
            row[
                "recommendation_json"
            ]
        ),
        "created_at": row[
            "created_at"
        ],
        "resolved_at": row[
            "resolved_at"
        ]
    }


def create_adaptation_proposal(
    user_id,
    evaluation
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_evaluation(
        evaluation
    )

    setup_adaptation_database()

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO adaptation_proposals (
                user_id,
                action,
                status,
                reason_codes_json,
                signals_json,
                recommendation_json
            )
            VALUES (
                ?,
                ?,
                'pending',
                ?,
                ?,
                ?
            )
            """,
            (
                user_id,
                evaluation[
                    "action"
                ],
                serialize_json(
                    evaluation[
                        "reason_codes"
                    ]
                ),
                serialize_json(
                    evaluation[
                        "signals"
                    ]
                ),
                serialize_json(
                    evaluation[
                        "recommendation"
                    ]
                )
            )
        )

        proposal_id = cursor.lastrowid

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM adaptation_proposals
            WHERE proposal_id = ?
              AND user_id = ?
            """,
            (
                proposal_id,
                user_id
            )
        ).fetchone()

        return row_to_adaptation_proposal(
            row
        )

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_adaptation_proposal(
    user_id,
    proposal_id
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        proposal_id,
        "proposal_id"
    )

    setup_adaptation_database()

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM adaptation_proposals
            WHERE proposal_id = ?
              AND user_id = ?
            """,
            (
                proposal_id,
                user_id
            )
        ).fetchone()

        return row_to_adaptation_proposal(
            row
        )

    finally:
        connection.close()


def get_user_adaptation_proposals(
    user_id,
    limit=20,
    status=None
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_limit(
        limit
    )

    if status is not None and status not in {
        "pending",
        "accepted",
        "rejected"
    }:
        raise ValueError("Invalid proposal status")

    setup_adaptation_database()

    connection = get_connection()

    try:
        if status is None:
            rows = connection.execute(
                """
                SELECT *
                FROM adaptation_proposals
                WHERE user_id = ?
                ORDER BY
                    created_at DESC,
                    proposal_id DESC
                LIMIT ?
                """,
                (
                    user_id,
                    limit
                )
            ).fetchall()

        else:
            rows = connection.execute(
                """
                SELECT *
                FROM adaptation_proposals
                WHERE user_id = ?
                  AND status = ?
                ORDER BY
                    created_at DESC,
                    proposal_id DESC
                LIMIT ?
                """,
                (
                    user_id,
                    status,
                    limit
                )
            ).fetchall()

        return [
            row_to_adaptation_proposal(
                row
            )
            for row in rows
        ]

    finally:
        connection.close()


def resolve_adaptation_proposal(
    user_id,
    proposal_id,
    resolution
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        proposal_id,
        "proposal_id"
    )

    if resolution not in VALID_RESOLUTION_STATUSES:
        raise ValueError("resolution must be accepted or rejected")

    setup_adaptation_database()

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM adaptation_proposals
            WHERE proposal_id = ?
              AND user_id = ?
            """,
            (
                proposal_id,
                user_id
            )
        ).fetchone()

        if row is None:
            return None

        if row[
            "status"
        ] != "pending":
            raise ValueError("Adaptation proposal has already been resolved")

        connection.execute(
            """
            UPDATE adaptation_proposals
            SET
                status = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE proposal_id = ?
              AND user_id = ?
              AND status = 'pending'
            """,
            (
                resolution,
                proposal_id,
                user_id
            )
        )

        connection.commit()

        updated_row = connection.execute(
            """
            SELECT *
            FROM adaptation_proposals
            WHERE proposal_id = ?
              AND user_id = ?
            """,
            (
                proposal_id,
                user_id
            )
        ).fetchone()

        return row_to_adaptation_proposal(
            updated_row
        )

    except:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_adaptation_proposal(
    user_id,
    proposal_id
):
    validate_positive_integer(
        user_id,
        "user_id"
    )

    validate_positive_integer(
        proposal_id,
        "proposal_id"
    )

    setup_adaptation_database()

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM adaptation_proposals
            WHERE proposal_id = ?
              AND user_id = ?
            """,
            (
                proposal_id,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except:
        connection.rollback()
        raise

    finally:
        connection.close()