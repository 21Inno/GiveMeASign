import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    yield app.test_client()

