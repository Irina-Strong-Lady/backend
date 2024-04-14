import pytest
from app import create_app

@pytest.fixture(scope='module')
def client():
    app = create_app('testing')
    test_client = app.test_client()

    with test_client as client:
        with app.app_context():
            yield client

