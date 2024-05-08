from .. import db
from . import auth
from .. models import User
from .. email import send_email
from .. decorators import secret_required
from flask import current_app, request, current_app, jsonify, render_template

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
    elif response[0]['confirmed']:
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
def confirm(token):
    user = User.get_user_by_confirmation_token(token)
    if not user:
        return render_template('auth/index.html', user=user)
    elif user:
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
            return user
        return render_template('auth/index.html', user=user)
    
@auth.route('/reset')
@secret_required
def reset():
    user = User()
    response_object = {}
    name, password = user.decode_user(request)
    phone = request.headers.get('phone')
    user = User.verify_user_by_phone(phone)
    if len(user.verify_users_by_password(password)) != 0:
        response_object['warning'] = 'warning'
        response_object['message'] = 'Недопустимый пароль. \
                                            Измените один или несколько символов'
    elif user and user.name == name:
        user.password = password
        token = user.generate_confirmation_token()
        send_email(current_app.config['APP_ADMIN'], 'Подтвердите изменение пароля',
                'auth/email/reset_job', user=user, token=token)
        response_object['warning'] = 'success'
        response_object['message'] = 'Заявка на изменение пароля направлена администратору'
    else:
        response_object['warning'] = 'warning'
        response_object['message'] = 'Ошибка в имени или номере телефона'
    return jsonify(response_object), 200

@auth.route('/password_reset/<token>')
def password_reset(token):
    user = User.get_user_by_reset_token(token)
    password_hash = User.get_hash_by_confirmation_token(token)
    if user:
        user.password_hash = password_hash
        db.session.add(user)
        db.session.commit()
        print('Изменение пароля подтверждено!')
    return render_template('auth/password_reset.html', user=user)