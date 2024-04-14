def test_new_user():
    from app import create_app
    from app.models import User
    app = create_app('testing')
    with app.app_context():
        user = User.query.filter_by(phone='+79000000001').first()
        assert user.name == 'Владимир'
        assert user.phone.__str__() == '8 (900) 000-00-01'
        assert user.confirmed == True
        assert user.verify_password('@Swordfish01') == True