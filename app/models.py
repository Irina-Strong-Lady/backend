import jwt
import os, re, base64
from app import db
from . import login_manager
from flask import current_app
from . email import send_email
from . telebot import send_message
from datetime import datetime, timedelta, timezone
from flask_login import UserMixin, AnonymousUserMixin
from sqlalchemy_utils.types.phone_number import PhoneNumberType
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    phone = db.Column(PhoneNumberType(region='RU', max_length=20))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone.__str__(),
            'password': self.password_hash,
            'confirmed': self.confirmed,
            'timestamp': self.timestamp
        }
    
    @property
    def password(self):
        raise AttributeError('Password is not readable attribute')
        
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def generate_users(cls):
        return cls.query.all()
    
    @classmethod
    def generate_users_by_name(cls, name):
        return cls.query.filter_by(name=name).all()
    
    def verify_users_by_password(self, password):
        users_list = list(filter(lambda item: item.verify_password(password), 
                                 self.generate_users()))
        return users_list
    
    def verify_user_by_password(self, name, password):
        users_list = list(filter(lambda item: item.verify_password(password), 
                                 self.generate_users_by_name(name)))
        return [item.serialize for item in users_list]
    
    @classmethod
    def verify_user_by_phone(cls, phone):
        return cls.query.filter_by(phone=phone).first()
    
    # Confirmation token section
    def generate_confirmation_token(self, expiration=3600):
        return jwt.encode({
                            'confirm': self.id,
                            'exp': datetime.now(tz=timezone.utc) + timedelta(seconds=expiration),
                            'password_hash': self.password_hash
                            },
                            current_app.config['SECRET_KEY'],
                            algorithm='HS256'
                          )
    
    @classmethod
    def get_user_by_confirmation_token(cls, token):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return False
        return cls.query.filter_by(id=data.get('confirm')).first()
    
    @classmethod
    def get_user_by_reset_token(cls, token):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'], options={'verify_signature': False})
        except:
            return False
        return cls.query.filter_by(id=data.get('confirm')).first()
    
    @classmethod
    def get_hash_by_confirmation_token(cls, token):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'], options={'verify_signature': False})
        except:
            return False
        return data.get('password_hash')

    def confirm(self, token):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True
    
    def decode_user(self, request):
        token = request.headers.get('Authorization')
        if token:
            token = token.replace('Basic ', '', 1)
            try:
                token = base64.b64decode(token)
                token = token.decode('utf-8')
            except TypeError:
                pass
            name, password = token.split(':')
            return name, password
        return None

class AnonymousUser(AnonymousUserMixin):
    pass    

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Visitor(db.Model):
    __tablename__ = 'visitors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    phone = db.Column(PhoneNumberType(region='RU', max_length=20))
    email = db.Column(db.String(128), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
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
            'phone': self.phone.__str__(),
            'email': self.email
        }
    
    def telebot_check_name(self, name, question):
        if bool(re.match('[а-яА-Я]', question)):
            self.name = name
            db.session.add(self)
            db.session.flush()
    
    def is_phone(self, question):
        return bool(re.match('^\\+?[1-9][0-9]{7,14}$', question))
    
    def telebot_check_phone(self, question, chat_id):
        phone_check = self.is_phone(question)
        question_fabula = self.query_question_db(chat_id)
        if question_fabula and phone_check:      
            self.phone = question
            db.session.add(self)
            send_message(chat_id, text=current_app.config['TELEBOT_END_MSG'])
            send_email(os.environ.get('APP_ADMIN'), 
                       current_app.config['TELEBOT_EMAIL_HEADER'], 
                       'mail/send_admin_telebot', name=self.name, 
                       phone=self.phone, question=question_fabula.message)
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
        return '<User %r>' % self.phone.__str__()
    
class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(128), nullable=True)
    fabula = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  
    user_id = db.Column(db.Integer, db.ForeignKey('visitors.id'))

    def __init__(self, user):
        try:
            self.user_id = user.id
        except AttributeError:
            print('Пользователь не существует')
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
        return '<Question %r>' % self.question_id

class Telegram(db.Model):
    __tablename__ = 'telegrams'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(128), nullable=True)
    message_id = db.Column(db.String(128), nullable=True)
    message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  
    user_id = db.Column(db.Integer, db.ForeignKey('visitors.id'))

    def __init__(self, user):
        try:
            self.user_id = user.id
        except AttributeError:
            print('Пользователь не существует')
            pass
    
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
        return '<Telebot %r>' % self.message_id