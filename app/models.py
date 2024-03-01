import os, re
from app import db
from flask import current_app
from datetime import datetime
from . telebot import send_message
from . email import send_email

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    phone = db.Column(db.String(128), nullable=True)
    email = db.Column(db.String(128), nullable=True)
    question = db.relationship('Question', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    telegram = db.relationship('Telegram', backref='author', lazy='dynamic', cascade='all, delete-orphan')
        
    @staticmethod
    def query_question_db(chat_id):
        fabula = Telegram.query.filter_by(chat_id=str(chat_id)).first()
        return fabula
    
    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
        }
    
    def telebot_check_name(self, name, question):
        if bool(re.match('[а-яА-Я]', question)):
            self.name = name
            db.session.add(self)
            db.session.flush()
    
    def telebot_check_phone(self, question, chat_id):
        phone_check = bool(re.match('^\\+?[1-9][0-9]{7,14}$', question))
        question_fabula = self.query_question_db(chat_id)
        if question_fabula and phone_check:      
            self.phone = question
            db.session.add(self)
            send_message(chat_id, text=current_app.config['TELEBOT_END_MSG'])
            # send_email(os.environ.get('APP_ADMIN'), 
            #            current_app.config['TELEBOT_EMAIL_HEADER'], 
            #            'mail/send_admin_telebot', name=self.name, 
            #            phone=self.phone, question=question_fabula.message)
        elif question_fabula and phone_check is False:
            send_message(chat_id, text=current_app.config['TELEBOT_PHONE_MSG'])
    
    def telebot_check_user_exist(self, name, question, chat_id, message_id):
        fabula = self.query_question_db(chat_id)
        if fabula:
            self = self.query.filter_by(id=fabula.user_id).first()
            self.telebot_check_phone(question, chat_id)
            db.session.commit()
        else:
            self.telebot_check_name(name, question)
            fabula = Telegram(self)
            fabula.telebot_check_question(question, chat_id, message_id)
            self.telebot_check_phone(question, chat_id)
            db.session.commit()
            
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
        try:
            self.user_id = user.id
        except AttributeError:
            print('Пользователь не был добавлен в БД до занесения своего вопроса')
            pass           
    
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

class Telegram(db.Model):
    __tablename__ = 'telegrams'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(128), nullable=True)
    message_id = db.Column(db.String(128), nullable=True)
    message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, user):
        self.user_id = user.id
    
    @property
    def serialize(self):
        return {
            'id': self.id,
            'question_id': self.chat_id,
            'fabula': self.message,
            'timestamp': self.timestamp
        }
    
    def telebot_check_question(self, question, chat_id, message_id):
        if bool(re.match('[а-яА-Я]', question)):
            self.chat_id = chat_id
            self.message_id = message_id
            self.message = question
            db.session.add(self)
            db.session.commit()
            send_message(chat_id, text=current_app.config['TELEBOT_CONFIRM_MSG'])

    def __repr__(self):
        return '<Telebot %r>' % self.id % self.user_id