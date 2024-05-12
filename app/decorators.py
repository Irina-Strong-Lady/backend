import os
from functools import wraps
from flask import json, request
from . response import MyResponse

def secret_decorator(secret):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.headers.get('secret') == secret:        
                return MyResponse(status=401, 
                            mimetype='application/json', 
                            response=json.dumps({'message': 'Invalid or missing secret'})
                            )
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def secret_required(f):
    SECRET = os.environ.get('SECRET')
    return secret_decorator(SECRET)(f)
