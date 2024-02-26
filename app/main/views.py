import os, re
import uuid
from flask_cors import CORS
from flask import json, request, current_app, \
                  jsonify, redirect, url_for, send_from_directory
from .. response import MyResponse
from . import main
from .. import db
from .. models import User, Question
from .. email import send_email
from .. telebot import send_message, get_from_env    
    
CORS(main, resources={r'/*': {'origins': '*'}})

'''Второй вариант с указанием фронтэнда с конкретным URL
   CORS(app, resources={r'/*': {'origins': 'http:// \
   loclhost:8080', "allow_headers": "Access-Control-Allow-Origin"}})'''

@main.route('/')
def index():
    print(get_from_env('TELEBOT'))
    return redirect(url_for('.questions'))    

@main.route('/questions', methods=['GET', 'POST'])
def questions():
    if not request.headers.get('secret') == os.environ.get('SECRET'):        
        return MyResponse(status=401, 
                        mimetype='application/json', 
                        response=json.dumps({'message': 'Invalid or missing secret'})
                        )
    users_list = User.query.all()    
    users = [item.serialize for item in users_list]
    questions_list = Question.query.all()    
    questions = [item.serialize for item in questions_list]
    response_object = {}   
    if request.method == 'POST':
        post_data = request.get_json()
        user = User.query.filter_by(phone=post_data.get('phone')).first()
        if not user:
            user = User(name = post_data.get('name'),
                        phone = post_data.get('phone'),
                        email = post_data.get('email'))
            db.session.add(user)
            db.session.commit()
            response_object['message_user'] = 'Пользователь добавлен в базу данных!'
        question = Question(user) 
        question.question_id = uuid.uuid4().hex, 
        question.fabula = post_data.get('question')
        db.session.add(question)        
        db.session.commit()
        response_object['message_question'] = 'Вопрос добавлен в базу данных!' 
        send_email(os.environ.get('APP_ADMIN'), f'Заявка № {question.id}', 'mail/send_admin', user=user, question=question)
        send_email(user.email, f'Номер Вашей заявки (заявка № {question.id})', 'mail/send_user', user=user, question=question)
    else:
        response_object['users'] = users
        response_object['questions'] = questions     
    return jsonify(response_object)

@main.route('/<id>', methods=['PUT', 'DELETE'])
def single_question(id):   
    response_object = {}
    if request.method == 'PUT':
        post_data = request.get_json()
        question = Question.query.filter_by(id=id).first()
        question.author.name=post_data.get('name') 
        question.author.phone=post_data.get('phone')
        question.author.email=post_data.get('email')
        question.fabula=post_data.get('question')
        db.session.add(question)
        db.session.commit()                
        response_object['message'] = 'Вопрос обновлен в базе данных!'
    if request.method == 'DELETE':
        question = Question.query.filter_by(id=id).first()
        db.session.delete(question)
        db.session.commit()
        response_object['message'] = f'Вопрос № {id} удален из базы данных!'
    return jsonify(response_object) 

@main.route('/process', methods=['POST'])
def process():
    if request.method == 'POST':
        name = request.json.get('message', 'Сообщение отсутствует').get('chat', 'Сведения о чате отсутствуют').get('last_name', 'клиент')
        question = request.json.get('message', 'Сообщение отсутствует').get('text', 'Сообщение отсутствует')
        chat_id = request.json.get('message', 'Сообщение отсутствует').get('chat', 'Сведения о чате отсутствуют').get('id', 'Сведения об id отсутствуют')
        if bool(re.search('[a-zA-Z]', question)):
            send_message(chat_id, text=f'Добрый день! Изложите Ваш вопрос.')
        else:
            send_message(chat_id, text=f'Уважаемый {name}! Спасибо, что выбрали услуги нашего Центра! Ваш вопрос принят в работу. Специалист свяжется с Вами!')
        return {'Ok': True} 

@main.route('/favicon.ico')
def favicon(): 
    return send_from_directory(os.path.join(current_app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')  