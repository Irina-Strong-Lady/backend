from .. import db
from . import auth
from . import auth_http
from .. models import User
from .. email import send_email
from .. decorators import secret_required
from flask import current_app, request, current_app, jsonify, render_template
from flask_login import login_user, logout_user, login_required, current_user

@auth.route('/')
def index():
    return render_template('auth/index.html')

@auth.route('/register')
@secret_required
def register():
    response_object = {}
    user = User()
    name, password = user.decode_user(request)
    phone = request.headers.get('phone')
    user = User.query.filter_by(phone=phone).first()
    if user:            
        if user.verify_password(password) and user.confirmed:
            user.name = name
            db.session.add(user)
            response_object['warning'] = 'success'
            response_object['message'] = f'Данные пользователя {phone} обновлены'
        elif user.verify_password(password) and not user.confirmed:
            token = user.generate_confirmation_token()
            send_email(current_app.config['APP_ADMIN'], 'Подтвердите регистрацию нового пользователя',
                    'auth/email/confirm_job', user=user, token=token)
            response_object['warning'] = 'success'
            response_object['message'] = 'Заявка повторно направлена администратору'
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
                    'auth/email/confirm_job', user=user, token=token)

            response_object['warning'] = 'success'
            response_object['message'] = 'Заявка направлена администратору'
        else:
            response_object['warning'] = 'warning'
            response_object['message'] = 'Недопустимый пароль. \
                                            Измените один или несколько символов'
    db.session.commit()
    return jsonify(response_object), 200   

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
        else:
            response_object['response'] = response
            response_object['warning'] = 'warning'
            response_object['message'] = f"Регистрация пользователя {response[0].get('name')} \
                                            требует подверждения администратором"
    return jsonify(response_object), 200

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    user = User.get_user_by_confirmation_token(token)
    if user:
        login_user(user)
        if user.confirmed:
            print('Аккаунт подтвержден')
        elif user.confirm(token):
            db.session.commit()
            print('Вы успешно подтвердили регистрацию нового сотрудника!')
            send_email(current_app.config['APP_ADMIN'], 
                    'Вы успешно подтвердили регистрацию нового сотрудника!',
                    'auth/email/confirmed_job', user=user)
        elif user.confirm(token) is False:
            user = user.confirm(token)
            print('Подтверждающая ссылка повреждена или истек срок её действия')
            return render_template('auth/index.html', user=user)
        return render_template('auth/index.html', user=user)

@auth.route('/logout')
@login_required
def logout(): 
    logout_user()
    return '<strong>The view function logout done!</strong>', 200