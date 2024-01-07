import os
basedir = os.path.abspath(os.path.dirname(__file__))
from main import app

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
                                        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

def create_db():
    from sqlalchemy import create_engine
    from sqlalchemy_utils import database_exists, create_database
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    if not database_exists(engine.url):
        create_database(engine.url)
    return create_database

if __name__ == '__main__':
    create_db()
