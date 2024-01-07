import os
basedir = os.path.abspath(os.path.dirname(__file__))

SECRET = os.environ.get('SECRET')

class Config:
    pass        

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    
    
config = {'development': DevelopmentConfig}
