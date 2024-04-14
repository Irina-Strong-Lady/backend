from .. import db
from . import auth
from . import auth_http
from .. models import User
from .. email import send_email
from .. decorators import secret_required
from flask import session, current_app, request, current_app, jsonify
from flask_login import current_user, logout_user, login_required

@auth.route('/')
def index():
    return '<strong>The view function index done!</strong>', 200

@auth_http.verify_password
@auth.route('/register')
@secret_required
def register():
    response_object = {}
    user = User()
    name, password = user.decode_user(request)
    phone = request.headers.get('phone')
    user = User.query.filter_by(phone=phone).first()
    if user:            
        if user.verify_password(password):
            user.name = name
            db.session.add(user)
            response_object['warning'] = 'success'
            response_object['message'] = f'Данные пользователя {phone} обновлены'
        else:
            response_object['warning'] = 'warning'
            response_object['message'] = 'У Вас нет прав на редактирование \
                                          этой учётной записи'
    elif not user:
        user = User(name=name, phone=phone, password=password)
        if len(user.verify_users_by_password(password)) == 0:
            db.session.add(user)
            db.session.commit()
            auth_http.current_user = user
            token = user.generate_confirmation_token()
            send_email(current_app.config['APP_ADMIN'], 'Подтвердите регистрацию нового пользователя',
                    'auth/email/confirm', user=user, token=token)

            response_object['warning'] = 'success'
            response_object['message'] = 'Заявка направлена администратору'
        else:
            response_object['warning'] = 'warning'
            response_object['message'] = 'Недопустимый пароль. \
                                            Измените один или несколько символов'
    db.session.commit()
    return jsonify(response_object), 200   

@auth_http.verify_password
@auth.route('/login')
@secret_required
def login():
    user = User()
    response_object = {}
    name, password = user.decode_user(request)
    users = User.generate_users_by_name(name)
    response = user.verify_user_by_password(name, password)
    if len(users) == 0:
        response_object['warning'] = 'warning'          
        response_object['message'] = 'Пользователь с таким именем не существует'
    elif len(users) > 0 and len(response) == 0:
        response_object['warning'] = 'warning'          
        response_object['message'] = f'Пароль пользователя {name} не совпадает'
    elif len(response) > 0:
        user = user.verify_users_by_password(password)[0]
        auth_http.current_user = user
        if response[0]['confirmed']:
            response_object['response'] = response
            response_object['warning'] = 'success'
            response_object['message'] = f"Добро пожаловать, {response[0].get('name')}"
            print(session.__dict__)
        else:
            response_object['response'] = response
            response_object['warning'] = 'warning'
            response_object['message'] = f"Регистрация пользователя {response[0].get('name')} \
                                            требует подверждения администратором"
    return jsonify(response_object), 200

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        print('Аккаунт подтвержден')
    elif current_user.confirm(token):
        db.session.commit()
        print('Вы успешно подтвердили регистрацию нового сотрудника!')
        send_email(current_app.config['APP_ADMIN'], 
                   'Вы успешно подтвердили регистрацию нового сотрудника!',
                   'auth/email/confirmed', user=current_user)
    else:
        print('Подтверждающая ссылка повреждена или истек срок её действия')
    return '<strong>The view function confirm done!</strong>', 200

@auth.route('/logout')
@login_required
def logout(): 
    logout_user()
    return '<strong>The view function logout done!</strong>', 200