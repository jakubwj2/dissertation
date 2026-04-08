import matplotlib
from flask_restful import Resource, fields, marshal_with, reqparse
from sqlalchemy.orm import joinedload

from app import db
from config import Checkpoint, load_settings
from kt.kt_service import KTService
from models.problem_log import ProblemLog
from models.user import Student

# from models.question import Question


matplotlib.use("Agg")

log_fields = {
    "log_id": fields.Integer,
    "student_id": fields.Integer,
    "correct": fields.Integer,
    "submission_time": fields.DateTime,
    "response_time": fields.Float,
    "question_id": fields.Integer,
}

settings = load_settings()
kt_service = KTService.create_from_ckpt(settings)


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


class KTPredictions(Resource):
    def get(self, student_id):
        student = (
            Student.query.filter_by(user_id=student_id)
            .options(joinedload(Student.problem_logs))
            .filter_by(user_id=student_id)
            .first_or_404()
        )
        sequence = kt_service.preprocess_data(student.problem_logs)
        probabilities = kt_service.predict_sequence(sequence)

        responses = sequence["shft_rseqs"].cpu().numpy()
        ids = sequence["shft_cseqs"].cpu().numpy()
        mask = sequence["masks"].cpu().numpy()

        model_name = kt_service.model_name
        dataset_name = kt_service.dataset_name

        return {
            "responses": responses.tolist(),
            "ids": ids.tolist(),
            "probabilities": probabilities.tolist(),
            "mask": mask.tolist(),
            "model_name": model_name,
            "dataset_name": dataset_name,
        }


model_fields = {
    "model_name": fields.String,
    "dataset_name": fields.String,
}
model_list_fields = {"models": fields.List(fields.Nested(model_fields))}
model_args = reqparse.RequestParser()
model_args.add_argument(
    "model_name", type=str, required=True, help="Model name is required"
)
model_args.add_argument(
    "dataset_name", type=str, required=True, help="Dataset name is required"
)


class Models(Resource):
    @marshal_with(model_list_fields)
    def get(self):
        return {"models": list(settings.checkpoints.values())}

    @marshal_with(model_fields)
    def post(self):
        global kt_service
        args = model_args.parse_args()
        ckpt_name = Checkpoint.create_ckpt_name(
            args["model_name"], args["dataset_name"]
        )
        if ckpt_name not in settings.checkpoints:
            return {"message": f"Model {ckpt_name} not found"}, 404

        kt_service = KTService.create_from_ckpt(settings, ckpt_name=ckpt_name)
        return kt_service


class GetCurrentModel(Resource):
    @marshal_with(model_fields)
    def get(self):
        global kt_service
        return kt_service
