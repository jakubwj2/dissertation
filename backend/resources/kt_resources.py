from flask_restful import Resource, reqparse, fields, marshal_with
from flask import make_response
from sqlalchemy.orm import joinedload
from io import BytesIO
import matplotlib
import matplotlib.pyplot as plt
import json
import logging


from app import db
from kt.kt_service import (
    KTService,
    CONFIG_PATH,
    MODEL_CONFIGS_PATH,
    DATA_CONFIG_PATH,
    DEVICE,
)
from kt.kt_utils import visualize_predictions

from models.problem_log import ProblemLog
from models.user import Student
# from models.question import Question

logger = logging.getLogger(__name__)

matplotlib.use("Agg")

log_fields = {
    "log_id": fields.Integer,
    "student_id": fields.Integer,
    "correct": fields.Integer,
    "submission_time": fields.DateTime,
    "response_time": fields.Float,
    "question_id": fields.Integer,
}

try:
    kt_config = json.load(open(CONFIG_PATH))
    data_config = json.load(open(DATA_CONFIG_PATH))
    model_configs = json.load(open(MODEL_CONFIGS_PATH))
except FileNotFoundError as e:
    logger.error(e)
    exit(1)
except json.JSONDecodeError as e:
    logger.error(e)
    exit(1)


kt_service = KTService.create(DEVICE, kt_config, data_config, model_configs)

interaction_args = reqparse.RequestParser()
interaction_args.add_argument(
    "correct", type=int, required=True, help="Correct is required"
)
interaction_args.add_argument(
    "skill_id", type=int, required=True, help="Skill id is required"
)
interaction_args.add_argument("response_time", type=float, required=True)


class RecommendExercise(Resource):
    def debug_question(self, question_id):
        operand_1 = question_id // 10
        operand_2 = question_id % 10
        return f"{operand_1} * {operand_2} =", operand_1 * operand_2

    def get(self, student_id):
        student = (
            Student.query.filter_by(user_id=student_id)
            .options(joinedload(Student.problem_logs))
            .filter_by(user_id=student_id)
            .first_or_404()
        )
        sequence = kt_service.preprocess_data(student.problem_logs)
        question_id = kt_service.suggest_next(sequence)
        question, answer = self.debug_question(question_id)
        return {
            "student_id": student_id,
            "question": {
                "text": question,
                "answer": answer,
                "skill_id": int(question_id),
            },
        }
        # question = Question.query.filter_by(question_id=question_id).first_or_404()
        # return question


class LogInteraction(Resource):
    @marshal_with(log_fields)
    def get(self, student_id):
        student = Student.query.filter_by(user_id=student_id).first_or_404()
        return student.problem_logs

    @marshal_with(log_fields)
    def post(self, student_id):
        args = interaction_args.parse_args()
        student = Student.query.filter_by(user_id=student_id).first()
        if student is None:
            return {"message": f"No student has id {student_id}"}, 404

        log = ProblemLog(
            student_id=student_id,
            correct=args["correct"],
            skill_id=args["skill_id"],
            response_time=args["response_time"],
            question_id=-0,
        )
        db.session.add(log)
        db.session.commit()

        # TODO: Predict next question here to minimize latency
        return log


class KTVisualization(Resource):
    def get(self, student_id):
        student = (
            Student.query.filter_by(user_id=student_id)
            .options(joinedload(Student.problem_logs))
            .filter_by(user_id=student_id)
            .first_or_404()
        )
        sequence = kt_service.preprocess_data(student.problem_logs)
        predictions = kt_service.predict_sequence(sequence)

        responses = sequence["shft_rseqs"].cpu().numpy()
        ids = sequence["shft_cseqs"].cpu().numpy()
        mask = sequence["masks"].cpu().numpy()

        visualize_predictions(responses, ids, predictions, mask)

        buf = BytesIO()
        fig = plt.gcf()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)

        resp = make_response(buf.getvalue())
        resp.headers["Content-Type"] = "image/png"
        return resp
