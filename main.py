import os
import uuid
from datetime import datetime
from config import config, SECRET
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, json, jsonify, request, send_from_directory

basedir = os.path.abspath(os.path.dirname(__file__))

config_name = os.environ.get('APP_CONFIG') or 'development'

app = Flask(__name__)
app.config.from_object(config[config_name])
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Form(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(128), nullable=True)
    name = db.Column(db.String(128), nullable=True)
    phone = db.Column(db.String(128), nullable=True)
    email = db.Column(db.String(128), nullable=True)
    question = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  
       
    @property
    def serialize(self):
        return {
            'id': self.question_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'question': self.question
        }
    
    def __repr__(self):
        return '<Form %r>' % self.phone % self.email

CORS(app, resources={r'/*': {'origins': '*'}})

'''Второй вариант с указанием фронтэнда с конкретным URL
   CORS(app, resources={r'/*': {'origins': 'http:// \
   loclhost:8080', "allow_headers": "Access-Control-Allow-Origin"}})'''

@app.route('/', methods=['GET', 'POST'])
def all_questions():
    if not request.headers.get('secret') == SECRET:
        return app.response_class(
            status=401,
            mimetype='application/json',
            response=json.dumps({'message': 'Invalid or missing secret'})
        )
    questions_list = Form.query.all()
    questions = [item.serialize for item in questions_list]
    response_object = {}
    if request.method == 'POST':
        post_data = request.get_json()
        questions = Form(question_id=uuid.uuid4().hex, 
                     name=post_data.get('name'), 
                     phone=post_data.get('phone'), 
                     email=post_data.get('email'),
                     question=post_data.get('question'))
        db.session.add(questions)
        db.session.commit()
        response_object['message'] = 'Вопрос добавлен в базу данных!' 
    else:
        response_object['questions'] = questions
    return jsonify(response_object)

@app.route('/<question_id>', methods=['PUT', 'DELETE'])
def single_question(question_id):   
    response_object = {}
    if request.method == 'PUT':
        post_data = request.get_json()
        question = Form.query.filter_by(question_id=question_id).first()
        question.name=post_data.get('name') 
        question.phone=post_data.get('phone')
        question.email=post_data.get('email')
        question.question=post_data.get('question')
        db.session.add(question)
        db.session.commit()                
        response_object['message'] = 'Вопрос обновлен в базе данных!'
    if request.method == 'DELETE':
        question = Form.query.filter_by(question_id=question_id).first()
        db.session.delete(question)
        db.session.commit()
        response_object['message'] = 'Вопрос удален из базы данных!'
    return jsonify(response_object)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5001')