import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET = os.environ.get('SECRET')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a5b88d557bee98d2b8ab356b01d6f41e'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    APP_ADMIN = os.environ.get('APP_ADMIN')
    APP_MAIL_SUBJECT_PREFIX = '["Центр правовой помощи при банкротстве"]'
    APP_MAIL_SENDER = os.environ.get('MAIL_USERNAME')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    TELEBOT_START_MSG = 'Добрый день! Изложите Ваш вопрос (прошу использовать русский язык)'
    TELEBOT_PHONE_MSG = 'Введите номер телефона в формате 79100000000 (11 цифр)'
    TELEBOT_CONFIRM_MSG = 'Ваш вопрос передан в работу'
    TELEBOT_END_MSG = 'Специалист свяжется с Вами в ближайшее время'
    TELEBOT_EMAIL_HEADER = 'Клиент обратился через Telegram'
    
    @staticmethod
    def init_app(app):
        pass

    @staticmethod
    def create_db():
        from sqlalchemy import create_engine
        from sqlalchemy_utils import database_exists, create_database
    
        if os.environ.get('DATABASE_URL') != None:
            engine = create_engine(os.environ.get('DATABASE_URL'))
            if not database_exists(engine.url):
                create_database(engine.url)
            return create_database

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_USE_TLS = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    Config.create_db()

class ProductionConfig(Config):
    DEBUG = False
    MAIL_USE_TLS = True
    Config.create_db() 

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}



