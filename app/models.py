from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    phone = db.Column(db.String(128), nullable=True)
    email = db.Column(db.String(128), nullable=True)
    question = db.relationship('Question', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
        }
    
    def __repr__(self):
        return '<User %r>' % self.id % self.name % self.phone
    
class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(128), nullable=True)
    fabula = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, user):
        self.user_id = user.id
    
    @property
    def serialize(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'fabula': self.fabula,
            'timestamp': self.timestamp
        }

    def __repr__(self):
        return '<Question %r>' % self.id % self.user_id