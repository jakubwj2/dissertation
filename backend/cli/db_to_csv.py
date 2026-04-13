import os

import pandas as pd
from sqlalchemy.orm import joinedload

from app import create_app, db
from models import ProblemLog, Question

DIR = "pykt-toolkit/data/smart_tutor"


def main():
    with create_app().app_context():
        logs = (
            db.session.query(ProblemLog)
            .options(
                joinedload(ProblemLog.question)
                .load_only(Question.external_id)  # type: ignore
                .joinedload(Question.skills)  # type: ignore
            )
            .all()
        )

        data = []
        columns = set(ProblemLog.__table__.columns) - {"question_id"}  # type: ignore
        for log in logs:
            skills_str = "_".join(sorted(skill.name for skill in log.question.skills))
            data.append(
                {
                    **{c.name: getattr(log, c.name) for c in columns},
                    "question_id": log.question.external_id,
                    "skills": skills_str,
                }
            )

        df = pd.DataFrame(data)
        os.makedirs(DIR, exist_ok=True)
        df.to_csv(os.path.join(DIR, "problem_logs.csv"), index=False)


if __name__ == "__main__":
    main()
