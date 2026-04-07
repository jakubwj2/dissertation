import os

import pandas as pd

from app import create_app, db
from models.problem_log import ProblemLog

DIR = "pykt-toolkit/data/smart_tutor"


def main():
    with create_app().app_context():
        connection = db.engine.connect()
        df = pd.read_sql(db.session.query(ProblemLog).statement, connection)

        os.makedirs(DIR, exist_ok=True)
        df.to_csv(os.path.join(DIR, "problem_logs.csv"), index=False)


if __name__ == "__main__":
    main()
