import os, re
import uuid
from flask import request, current_app, \
                  jsonify, send_from_directory
from . import main
from .. import db
from .. models import User, Visitor, Question, Telegram
from .. email import send_email
from .. telebot import send_message
from .. decorators import secret_required
    
@main.route('/')
def index():
    return jsonify({'message': 'Backend-сервер сайта https://irina23new.ru. Доступ разрешен только техническому персоналу'})

@main.route('/favicon.ico')
def favicon(): 
    return send_from_directory(os.path.join(current_app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon') 

@main.route('/visitors', methods=['GET', 'POST'])
@secret_required
def visitors():
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
            response_object['message'] = 'Посетитель добавлен в базу данных'
        else: 
            response_object['message'] = 'Посетитель уже существует'
        db.session.commit()
    else:
        response_object['warning'] = 'error'
        response_object['message'] = 'Внутренняя ошибка сервера. Попробуйте позже'
    return jsonify(response_object)

@main.route('/questions', methods=['GET', 'POST'])
@secret_required
def questions():    
    response_object = {}   
    if request.method == 'POST': 
        post_data = request.get_json() 
        visitor = Visitor.query.filter_by(phone=post_data.get('phone')).first()      
        question = Question(visitor) 
        question.question_id = uuid.uuid4().hex, 
        question.fabula = post_data.get('question')
        db.session.add(question)        
        db.session.commit()
        response_object['warning'] = 'success'
        response_object['message'] = 'Успешно! Ваш вопрос передан в обработку'
        send_email(os.environ.get('APP_ADMIN'), f'Заявка № {question.id}', 'mail/send_admin', visitor=visitor, question=question)
        if visitor.email != '':
            send_email(visitor.email, f'Номер Вашей заявки (заявка № {question.id})', 'mail/send_user', visitor=visitor, question=question)
    else:
        response_object['warning'] = 'error'
        response_object['message'] = 'Внутренняя ошибка сервера. Попробуйте позже' 
    return jsonify(response_object)

@main.route('/questions_list')
@secret_required
def get_merge_list():    
    response_object = {} 
    if request.method == 'GET':
        data = Question.merge_serialized_data()
        response_object['response'] = data
    return jsonify(response_object)

@main.route('/question_update/<question_id>', methods=['PUT', 'DELETE'])
@secret_required
def single_question(question_id):   
    response_object = {}
    if request.method == 'PUT':
        post_data = request.get_json()
        question = Question.query.filter_by(question_id=question_id).first()
        if question:
            if post_data.get('fabula') != None:
                question.fabula=post_data.get('fabula')
            if post_data.get('archive') != None:
                question.archive=post_data.get('archive')                    
            if post_data.get('id') != None:
                question.executor_id = post_data.get('id')
            db.session.add(question)
            db.session.commit()                
            response_object['warning'] = 'success'
            response_object['message'] = 'Данные обновлены!' 
        telegram = Telegram.query.filter_by(message_id=question_id).first()
        if telegram:
            if post_data.get('fabula') != None:
                telegram.message=post_data.get('fabula')
            if post_data.get('archive') != None:
                telegram.archive=post_data.get('archive')                    
            if post_data.get('id') != None:
                telegram.executor_id = post_data.get('id')
            db.session.add(telegram)
            db.session.commit()                
            response_object['warning'] = 'success'
            response_object['message'] = 'Данные обновлены!'
    if request.method == 'DELETE':
        question = Question.query.filter_by(question_id=question_id).first()
        if question:
            db.session.delete(question)
            db.session.commit()
            response_object['warning'] = 'success'
            response_object['message'] = f'Вопрос № {question.id} удален из базы данных!'
        telegram = Telegram.query.filter_by(message_id=question_id).first()
        if telegram:
            db.session.delete(telegram)
            db.session.commit()
            response_object['warning'] = 'success'
            response_object['message'] = f'Вопрос № {telegram.id} удален из базы данных!'
    return jsonify(response_object)

@main.route('/telegrams', methods=['GET', 'POST'])
def telegrams():
    visitor = Visitor()
    telegrams_list = Telegram.query.all()    
    telegrams = [item.serialize for item in telegrams_list]
    response_object = {}
    if request.method == 'POST' and 'message' in request.json \
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