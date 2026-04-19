import random

import matplotlib
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource, fields, marshal_with, reqparse
from shared.user_type import UserType
from sqlalchemy.orm import joinedload

from app import db
from auth.decorators import role_required
from config.checkpoint import Checkpoint
from config.settings import Settings
from kt.kt_service import KTService
from models import ProblemLog, Question, Skill, Student
from question.question_service import QuestionService

# from models.question import Question


matplotlib.use("Agg")


settings = Settings.load()
kt_service = KTService.create_from_ckpt(settings)
question_service = QuestionService()


class RecommendExercise(Resource):
    method_decorators = [jwt_required(), role_required(UserType.STUDENT)]

    def get(self):
        student_id = get_jwt_identity()
        # student = (
        #     Student.query.filter_by(id=student_id)
        #     .options(joinedload(Student.problem_logs))
        #     .filter_by(id=student_id)
        #     .first_or_404()
        # )
        # sequence = kt_service.preprocess_data(student.problem_logs)
        # question_id = kt_service.suggest_next(sequence)
        # question = question_service.generate_question(question_id)

        coverage_questions = question_service.generate_coverage_questions()
        if len(coverage_questions) > 0:
            question_id = random.choice(coverage_questions)
            question = question_service.generate_question(question_id)
        else:
            question = question_service.generate_random_question()

        return {
            "student_id": student_id,
            "question": {
                "text": question.question_text,
                "skills": [skill.name for skill in question.skills],
                "question_id": question.id,
            },
        }


interaction_log_args = reqparse.RequestParser()
interaction_log_args.add_argument("answer", type=float, required=True)
interaction_log_args.add_argument("question_id", type=str, required=True)
interaction_log_args.add_argument("response_time", type=float, required=True)

log_fields = {
    "id": fields.Integer,
    "student_id": fields.Integer,
    "correct": fields.Integer,
    "submission_time": fields.DateTime,
    "response_time": fields.Float,
    "question_id": fields.Integer,
}


class LogInteraction(Resource):
    method_decorators = [role_required(UserType.STUDENT)]

    @marshal_with(log_fields)
    def get(self):
        student_id = get_jwt_identity()
        student = Student.query.filter_by(id=student_id).first_or_404()
        return student.problem_logs

    @marshal_with(log_fields)
    def post(self):
        student_id = get_jwt_identity()

        args = interaction_log_args.parse_args()
        student = Student.query.filter_by(id=student_id).first()
        if student is None:
            return {"message": f"No student has id {student_id}"}, 404

        question = db.session.get(Question, args["question_id"])
        if question is None:
            return {"message": f"No question has id {args['question_id']}"}, 404

        correct = round(args["answer"], 3) == round(float(question.answer), 3)  # type: ignore

        log = ProblemLog(
            student_id=student_id,
            correct=correct,
            response_time=args["response_time"],
            question_id=args["question_id"],
        )
        db.session.add(log)
        db.session.commit()

        # TODO: Predict next question here to minimize latency
        return log


class KTPredictions(Resource):
    method_decorators = [role_required(UserType.STUDENT)]

    def get(self):
        student_id = get_jwt_identity()
        student = (
            Student.query.filter_by(id=student_id)
            .options(joinedload(Student.problem_logs))
            .filter_by(id=student_id)
            .first_or_404()
        )
        sequence = kt_service.preprocess_data(student.problem_logs)
        probabilities = kt_service.predict_sequence(sequence)

        responses = sequence["shft_rseqs"].cpu().numpy()
        ids = sequence["shft_cseqs"].cpu().numpy()
        mask = sequence["masks"].cpu().numpy()

        model_name = kt_service.ckpt.model_name
        dataset_name = kt_service.ckpt.dataset_name

        ids = [log.question.skills[0].name for log in student.problem_logs[1:]]
        ids = [ids + [0] * (probabilities.shape[1] - len(ids))]
        return {
            "responses": responses.tolist(),
            "ids": ids,
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


class Skills(Resource):
    def get(self):
        return [skill.name for skill in Skill.query.all()]
