# StudyHub_Project/app/models.py
from . import db
from datetime import datetime

class TestSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    score_percentage = db.Column(db.Float, nullable=True) 
    total_questions_in_session = db.Column(db.Integer, nullable=True)
    correct_answers_in_session = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='in_progress') 
    last_question_idx_viewed = db.Column(db.Integer, nullable=True, default=0)
    responses = db.relationship('UserResponse', backref='test_session', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<TestSession id={self.id} status={self.status} date={self.timestamp.strftime("%Y-%m-%d %H:%M")} score={self.score_percentage}%>'

class UserResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_session_id = db.Column(db.Integer, db.ForeignKey('test_session.id'), nullable=False)
    question_id_original = db.Column(db.String(80), nullable=False)
    # Armazena as respostas do usuário como uma string JSON de uma lista de letras. Ex: '["A", "D"]'
    user_answers_letters_json = db.Column(db.String(50), nullable=False) 
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserResponse q:{self.question_id_original} ans_json:{self.user_answers_letters_json} correct:{self.is_correct}>'