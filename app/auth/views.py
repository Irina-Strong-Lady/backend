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
                    'auth/email/confirm', user=user, token=token)
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
                    'auth/email/confirm', user=user, token=token)

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
        user = user.verify_users_by_password(password)[0]
        token = user.generate_confirmation_token()
        response_object['token'] = token
        response_object['warning'] = 'success'
        response_object['message'] = f"Добро пожаловать, {response[0].get('name')}"
    else:
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
                    'auth/email/confirmed', user=user)
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
                'auth/email/reset', user=user, token=token)
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

@auth.route('/profile', methods=['PUT'])
@secret_required
def profile():
    response_object = {}
    if request.method == 'PUT':
        post_data = request.get_json()
        name = post_data.get('name')
        phone = post_data.get('phone')
        new_phone = post_data.get('newPhone')
        user = User.verify_user_by_phone(phone)
        if user:
            if name != '' and name is not None:
                user.name = name
                db.session.add(user)
                response_object['warning'] = 'success'
                response_object['message'] = f'Данные пользователя {phone} обновлены'
            if new_phone != '' and new_phone is not None:
                user.phone = new_phone
                db.session.add(user)
                response_object['warning'] = 'success'
                response_object['message'] = f'Данные пользователя {new_phone} обновлены'
        else:
            response_object['warning'] = 'warning'
            response_object['message'] = 'Пользователь не существует'    
        db.session.commit()
    return jsonify(response_object), 200

@auth.route('/role_update/<id>', methods=['PUT'])
@secret_required
def role_update(id):
    response_object = {}
    if request.method == 'PUT':
        post_data = request.get_json()
        user = User.query.filter_by(id=id).first()
        if user:
            if post_data.get('role') != None:
                role = post_data.get('role')
                user.admin = role
                db.session.add(user)
                db.session.commit()
                response_object['warning'] = 'success'
                response_object['message'] = 'Данные обновлены!'                   
    return jsonify(response_object)

@auth.route('/user_delete/<id>', methods=['DELETE'])
@secret_required
def user_delete(id):
    from sqlalchemy.exc import IntegrityError
    response_object = {}
    if request.method == 'DELETE':
        if id == 'undefined':
            response_object['warning'] = 'warning'
            response_object['message'] = 'Выберите профиль пользователя' 
        else:              
            user = User.query.filter_by(id=id).first()
            if user:
                db.session.delete(user)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()          
                response_object['warning'] = 'success'
                response_object['message'] = f'Аккаунт пользователя {user.name} {user.phone} удален!'                  
    return jsonify(response_object)

