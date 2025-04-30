from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    options = db.Column(db.String(500))  # comma-separated for MCQs
    correct_answer = db.Column(db.String(255))
    question_type = db.Column(db.String(50))  # "mcq" or "short"