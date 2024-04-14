from flask import Blueprint
from flask_httpauth import HTTPBasicAuth

auth = Blueprint('auth', __name__)

auth_http = HTTPBasicAuth()

from app.auth import views, authentictation