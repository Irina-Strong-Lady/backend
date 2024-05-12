from . import auth
from ..models import User

@auth.after_request
def add_bearer_token(response):
    data = response.get_data(as_text=True)
    if 'success' in data:
        user = User()
        token = user.generate_confirmation_token()
        response.headers['Authorization'] = f'Basic {token}'
    return response