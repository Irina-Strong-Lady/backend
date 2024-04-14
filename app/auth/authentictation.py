from . import auth
from flask_login import login_user
from . import auth_http

@auth.after_request 
def test(response):
    if hasattr(auth_http.current_user, 'is_active'):
        user = auth_http.current_user
        login_user(user)
    return response