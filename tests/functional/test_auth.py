import time
from flask import session, url_for
from base64 import b64encode
from app.models import User
from flask_login import current_user, login_user

def test_auth_index_page(client):
    response = client.get(url_for('auth.index', _external=True))
    assert response.status_code == 200
    assert b'<strong>The view function index done!</strong>' in response.data

def test_auth_register_page_new_user_success(client):
    user = User()
    name = 'Александр'
    password = '@Swordfish06'
    phone='+79000000006'
    secret = 'swordfish1'
    data = f'{name}:{password}' # Пользователь успешно регистрируется впервые
    if user.verify_user_by_password(name, password):
        print('Пользователь уже существует')
    else:        
        data = data.encode('utf-8')
        data = b64encode(data)
        encoded = data.decode('utf-8')
        headers = {'Authorization': 'Basic ' + encoded, 'phone': phone, 'secret': secret}
        response = client.get(url_for('auth.register', _external=True), headers=headers).get_json()
        assert response['message'] == 'Заявка направлена администратору'
        assert response['warning'] == 'success'
    
def test_auth_register_page_success(client):
    data = 'Николай:@Swordfish01' # Все учётные данные подходят (пользователь уже зарегистрирован)
    data = data.encode('utf-8')
    data = b64encode(data)
    encoded = data.decode('utf-8')
    secret = 'swordfish1'
    phone='+79000000001'
    headers = {'Authorization': 'Basic ' + encoded, 'phone': phone, 'secret': secret}
    response = client.get(url_for('auth.register', _external=True), headers=headers).get_json()
    assert response['message'] == f'Данные пользователя {phone} обновлены'
    assert response['warning'] == 'success'

def test_auth_register_page_no_rights_warning(client):
    data = 'Владимир:@Swordfish02' # Не совпадает пароль
    data = data.encode('utf-8')
    data = b64encode(data)
    encoded = data.decode('utf-8')
    secret = 'swordfish1'
    phone='+79000000001'
    headers = {'Authorization': 'Basic ' + encoded, 'phone': phone, 'secret': secret}
    response = client.get(url_for('auth.register', _external=True), headers=headers).get_json()
    assert response['message'] == 'У Вас нет прав на редактирование \
                                          этой учётной записи'
    assert response['warning'] == 'warning'

def test_auth_register_page_new_name_success(client):
    data = 'Владимир:@Swordfish01' # Новое имя пользователя при попытке повтороной регистрации,
    data = data.encode('utf-8')    # если пароль и номер телефона корректны
    data = b64encode(data)
    encoded = data.decode('utf-8')
    secret = 'swordfish1'
    phone='+79000000001'
    headers = {'Authorization': 'Basic ' + encoded, 'phone': phone, 'secret': secret}
    response = client.get(url_for('auth.register', _external=True), headers=headers).get_json()
    assert response['message'] == f'Данные пользователя {phone} обновлены'
    assert response['warning'] == 'success'

def test_auth_login_page_non_exist_user_warning(client):
    data = 'Ипполит:@Swordfish01' # Введено несуществующее имя пользователя
    data = data.encode('utf-8')
    data = b64encode(data)
    encoded = data.decode('utf-8')
    secret = 'swordfish1'
    headers = {'Authorization': 'Basic ' + encoded, 'secret': secret}
    response = client.get(url_for('auth.login', _external=True), headers=headers).get_json()
    assert response['message'] == 'Пользователь с таким именем не существует'
    assert response['warning'] == 'warning'

def test_auth_login_page_incorrect_password_warning(client):
    name = 'Владимир'
    data = f'{name}:@Swordfish04' # Введен некорректный пароль,
    data = data.encode('utf-8')    # при корректно введенном имени
    data = b64encode(data)
    encoded = data.decode('utf-8')
    secret = 'swordfish1'
    headers = {'Authorization': 'Basic ' + encoded, 'secret': secret}
    response = client.get(url_for('auth.login', _external=True), headers=headers).get_json()
    assert response['message'] == f'Пароль пользователя {name} не совпадает'
    assert response['warning'] == 'warning'

def test_auth_login_page_all_correct_credentials_success(client):
    user = User()
    name = 'Владимир'
    password = '@Swordfish01'
    resp = user.verify_user_by_password(name, password)
    data = f'{name}:{password}' # Все данные при входе введены корректно
    data = data.encode('utf-8') # и пользователь подтвержден администратором  
    data = b64encode(data)
    encoded = data.decode('utf-8')
    secret = 'swordfish1'
    headers = {'Authorization': 'Basic ' + encoded, 'secret': secret}
    response = client.get(url_for('auth.login', _external=True), headers=headers).get_json()
    resp[0]['timestamp'] = resp[0]['timestamp'].strftime('%a, %d %b %Y %H:%M:%S GMT') # Перевод объекта datetime в строковый формат 'Sat, 13 Apr 2024 06:31:17 GMT'
    assert response['response'] == resp
    assert response['message'] == f'Добро пожаловать, {name}'
    assert response['warning'] == 'success'

def test_auth_login_page_user_unconfirmed_warning(client):
    user = User()
    name = 'Александр'
    password = '@Swordfish06'
    resp = user.verify_user_by_password(name, password)
    data = f'{name}:{password}' # Все данные при входе введены корректно,
    data = data.encode('utf-8') # но пользователь не подтвержден администратором
    data = b64encode(data)
    encoded = data.decode('utf-8')
    secret = 'swordfish1'
    headers = {'Authorization': 'Basic ' + encoded, 'secret': secret}
    response = client.get(url_for('auth.login', _external=True), headers=headers).get_json()
    resp[0]['timestamp'] = resp[0]['timestamp'].strftime('%a, %d %b %Y %H:%M:%S GMT') # Перевод объекта datetime в строковый формат 'Sat, 13 Apr 2024 06:31:17 GMT'
    assert response['response'] == resp
    assert response['message'] == f"Регистрация пользователя {name} \
                                            требует подверждения администратором"
    assert response['warning'] == 'warning'

def test_auth_confirm_page_already_confirmed_print(client, capfd):
    password = '@Swordfish05' # Пользователь уже был подтвержден администратором (confirmed=True в БД)
    users = User.query.all()
    for item in users:
        if item.verify_password(password):
            login_user(item)
            token = item.generate_confirmation_token(expiration=3600)
            client.get(url_for('auth.confirm', token=token, _external=True))
            out, err = capfd.readouterr()
            assert out == 'Аккаунт подтвержден\n'

def test_auth_confirm_page_confirmed_print(client, capfd):
    password = '@Swordfish04' # Пользователь ещё не был подтвержден администратором (confirmed=False в БД)
    users = User.query.all()  # В процессе теста происходит фактическая регистрация (confirmed=True в БД)
    for item in users:
        if item.verify_password(password):
            login_user(item)
            token = item.generate_confirmation_token(expiration=3600)
            client.get(url_for('auth.confirm', token=token, _external=True))
            out, err = capfd.readouterr()
            assert out == 'Вы успешно подтвердили регистрацию нового сотрудника!\n'

def test_auth_confirm_page_token_expired_print(client, capfd):
    password = '@Swordfish06' # Пользователь ещё не был подтвержден администратором (confirmed=False в БД)
    users = User.query.all()  # но token истек
    for item in users:
        if item.verify_password(password):
            login_user(item)
            token = item.generate_confirmation_token(expiration=0) # Токен истек
            time.sleep(2)
            client.get(url_for('auth.confirm', token=token, _external=True))
            out, err = capfd.readouterr()
            assert out == 'Подтверждающая ссылка повреждена или истек срок её действия\n'

def test_auth_confirm_page_token_invalid_print(client, capfd):
    password = '@Swordfish06' # Пользователь ещё не был подтвержден администратором (confirmed=False в БД)
    users = User.query.all()  # token поврежден
    for item in users:
        if item.verify_password(password):
            login_user(item)
            token = item.generate_confirmation_token(expiration=3600)
            token = token[:-1]
            client.get(url_for('auth.confirm', token=token, _external=True))
            out, err = capfd.readouterr()
            assert out == 'Подтверждающая ссылка повреждена или истек срок её действия\n'

def test_auth_logout(client):
    assert session != {}
    client.get(url_for('auth.logout'))
    assert session != {}