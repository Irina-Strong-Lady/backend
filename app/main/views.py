import os, re
import uuid
from flask_cors import CORS
from flask import request, current_app, \
                  jsonify, send_from_directory
from . import main
from .. import db
from .. models import User, Visitor, Question, Telegram
from .. email import send_email
from .. telebot import send_message
from .. decorators import secret_required
    
CORS(main, resources={r'/*': {'origins': '*'}})

@main.route('/')
@secret_required
def index():
    return jsonify({'message': 'Backend-сервер сайта https://irina23new.ru. Доступ разрешен только техническому перосналу'})

@main.route('/register', methods=['GET', 'POST'])
@secret_required
def register():
    response_object = {}   
    if request.method == 'POST':
        post_data = request.get_json()
        user = User.query.filter_by(phone=post_data.get('phone')).first()
        if user:
            user.name = post_data.get('name')
            db.session.add(user)
        if not user:
            user = User(**post_data)
            db.session.add(user)
            response_object['users'] = 'Заявка направлена администратору'
        else: 
            response_object['users'] = 'Пользователь уже существует'
        db.session.commit()
    return jsonify(response_object)

@main.route('/login', methods=['GET', 'POST'])
@secret_required
def login():    
    response_object = {}
    users_list = []
    if request.method == 'POST':
        post_data = request.get_json()
        name = post_data.get('name')
        password = post_data.get('password')
        users = User.query.filter_by(name=name).all()
        if users != []:
            for item in users:
                user = item.verify_password(password)
                if user:            
                    users_list.append(item)
                    users = [item.serialize for item in users_list]
                    response_object['users'] = users
                return jsonify(response_object)

@main.route('/visitors', methods=['GET', 'POST'])
@secret_required
def visitors():
    visitors_list = Visitor.query.all()    
    visitors = [item.serialize for item in visitors_list]
    response_object = {}   
    if request.method == 'POST':
        post_data = request.get_json()
        visitor = Visitor.query.filter_by(phone=post_data.get('phone')).first()
        if visitor:
            visitor.name = post_data.get('name')
            visitor.email = post_data.get('email')
            db.session.add(visitor)
        if not visitor:
            del post_data['question']
            visitor = Visitor(**post_data)
            db.session.add(visitor)
            response_object['message'] = 'Посетитель добавлен в базу данных!'
        else: 
            response_object['message'] = 'Посетитель уже существует!'
        db.session.commit()
    else:
        response_object['visitors'] = visitors
    return jsonify(response_object)

@main.route('/questions', methods=['GET', 'POST'])
@secret_required
def questions():
    questions_list = Question.query.all()    
    questions = [item.serialize for item in questions_list]
    response_object = {}   
    if request.method == 'POST': 
        post_data = request.get_json() 
        visitor = Visitor.query.filter_by(phone=post_data.get('phone')).first()      
        question = Question(visitor) 
        question.question_id = uuid.uuid4().hex, 
        question.fabula = post_data.get('question')
        db.session.add(question)        
        db.session.commit()
        response_object['message'] = 'Вопрос добавлен в базу данных!'
        # send_email(os.environ.get('APP_ADMIN'), f'Заявка № {question.id}', 'mail/send_admin', visitor=visitor, question=question)
        # if visitor.email != '':
        #     send_email(visitor.email, f'Номер Вашей заявки (заявка № {question.id})', 'mail/send_user', visitor=visitor, question=question)
    else:
        response_object['questions'] = questions     
    return jsonify(response_object)

@main.route("/telegrams", methods=["GET", "POST"])
def telegrams():
    visitor = Visitor()
    telegrams_list = Telegram.query.all()    
    telegrams = [item.serialize for item in telegrams_list]
    response_object = {}
    if request.method == "POST" and 'message' in request.json \
        and 'text' in request.json['message']:
        name = request.json['message']['chat']['last_name']        
        question = request.json['message']['text'] 
        chat_id= request.json['message']['chat']['id']
        message_id = request.json['message']['message_id']
        if question == '/start' or bool(re.match('[a-zA-Z]', question)):
            send_message(chat_id, text=current_app.config['TELEBOT_START_MSG'])
        visitor.telebot_check_user_exist(name, question, chat_id, message_id)
    else:
        response_object['telegrams'] = telegrams
        print('Message or text key is not in request.json')
    return jsonify(response_object)       

@main.route('/favicon.ico')
def favicon(): 
    return send_from_directory(os.path.join(current_app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon') 


# @main.route('/<id>', methods=['PUT', 'DELETE'])
# def single_question(id):   
#     response_object = {}
#     if request.method == 'PUT':
#         post_data = request.get_json()
#         question = Question.query.filter_by(id=id).first()
#         question.author.name=post_data.get('name') 
#         question.author.phone=post_data.get('phone')
#         question.author.email=post_data.get('email')
#         question.fabula=post_data.get('question')
#         db.session.add(question)
#         db.session.commit()                
#         response_object['message'] = 'Вопрос обновлен в базе данных!'
#     if request.method == 'DELETE':
#         question = Question.query.filter_by(id=id).first()
#         db.session.delete(question)
#         db.session.commit()
#         response_object['message'] = f'Вопрос № {id} удален из базы данных!'
#     return jsonify(response_object) 
 