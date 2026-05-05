import pandas as pd
from app import create_app, db


def print_student_sequence_mean_correlation():
    query = """
SELECT
    pl.submission_time AS timestamp,
    stu.id AS student_id,
    pl.correct AS correct,
    s.model_name AS synthesizer
FROM problem_logs pl
JOIN students stu ON stu.id = pl.student_id
JOIN synthesizers s ON s.id = stu.synthesizer_id
"""

    df = pd.read_sql(query, db.engine)
    df = df.sort_values(["synthesizer", "student_id", "timestamp"])

    usecols = {
        "user_id": "student_id",
        "correct": "correct",
        "order_id": "timestamp",
    }
    assist_df = pd.read_csv(
        "pykt-toolkit/data/assist2009/skill_builder_data_corrected_collapsed.csv",
        usecols=list(usecols.keys()),
    )
    assist_df = assist_df.rename(columns=usecols)
    assist_df["synthesizer"] = "assist2009"

    df = pd.concat([df, assist_df])

    df["interaction_index"] = df.groupby(["synthesizer", "student_id"]).cumcount()

    # agg = df.groupby(["synthesizer"])["interaction_index"].value_counts().reset_index()
    agg = (
        df.groupby(["synthesizer", "interaction_index"])
        .first()
        .reset_index()[["synthesizer"]]
        .value_counts()
    )
    print(int(agg.min()))
    df = df[df["interaction_index"] < agg.min()]

    agg = (
        df.groupby(["synthesizer", "interaction_index"])["correct"]
        .mean()
        .reset_index()
        .rename(columns={"correct": "accuracy"})
    )
    print(agg["interaction_index"].value_counts())
    curve = agg.pivot(
        index="interaction_index", columns="synthesizer", values="accuracy"
    )
    print(curve.corr(method="pearson"))


def print_question_difficulty_comparison():
    query = """
SELECT
q.external_id as question_id,
stu.id AS student_id,
pl.correct AS correct,
s.model_name
FROM problem_logs pl
JOIN students stu ON stu.id = pl.student_id
JOIN synthesizers s ON s.id = stu.synthesizer_id
Join questions q on q.id = pl.question_id;
"""

    df = pd.read_sql(query, db.engine)

    agg = (
        df.groupby(["model_name", "question_id"])["correct"]
        .mean()
        .reset_index()
        .rename(columns={"correct": "accuracy"})
    )
    # return agg.sort_values("accuracy")
    pt = agg.pivot(index="question_id", columns="model_name", values="accuracy")
    print(pt.corr())


def print_question_answer_bias():
    query = """
    SELECT
    q.external_id as question_id,
    stu.id AS student_id,
    pl.correct AS correct,
    s.model_name,
    sk.name AS skill
    FROM problem_logs pl
    JOIN students stu ON stu.id = pl.student_id
    JOIN synthesizers s ON s.id = stu.synthesizer_id
    Join questions q on q.id = pl.question_id
    JOIN questions_skills qs ON qs.question_id = q.id
    JOIN skills sk on sk.id = qs.skill_id;
    """

    df = pd.read_sql(query, db.engine)
    # group = df.groupby(["model_name", "skill"])["correct"]
    # agg = (
    #     (group.count() - group.sum())
    #     .reset_index()
    #     .rename(columns={"correct": "accuracy"})
    # )
    # pt = agg.pivot(index="skill", columns="model_name", values="accuracy")

    group = df.groupby(["model_name", "skill"])["correct"]
    agg = group.mean().reset_index()
    pt = agg.pivot(index="skill", columns="model_name", values="correct")

    print(pt.to_latex(float_format="%.4g"))


if __name__ == "__main__":
    with create_app().app_context():
        print_student_sequence_mean_correlation()

        print_question_answer_bias()
        print_question_difficulty_comparison()
