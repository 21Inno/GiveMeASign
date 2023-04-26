import os
import sys
topdir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(topdir)

from flask_login import current_user
from app.models import Group, User, Admin 
from app import db,app


def test_login(client):
    # Test avec des informations de connexion invalides
    response = client.post('/login/', data=dict(
        group='Invalid group',
        username='Invalid user',
        password='Invalid password'
    ))
    assert response.status_code == 400

    # Test avec un groupe inexistant
    response=client.post('/login/', data=dict(
        group = 'Sacre-coeur',
        username='baba',
        password="StMarie"
    ))
    assert response.status_code == 400


def test_register_admin(client):   
    response = client.post('/register_admin/', data={
        'username': 'user1',
        'email': 'user1@test.com',
        'password': 'password1',
        'checkpassword': 'password1'
    }, follow_redirects=True)
    assert current_user.is_authenticated

    response = client.post('/login_admin/', data={
        'username': 'user2',
        'email': 'user2@test.com',
        'password': 'password2',
        'checkpassword': 'password2'
    }, follow_redirects=True)
    assert current_user.is_authenticated

    # Try to register a user with the same username as user1
    response = client.post('/register_admin/', data={
        'username': 'user1',
        'email': 'user3@test.com',
        'password': 'password3',
        'checkpassword': 'password3'
    }, follow_redirects=True)
    assert b'This username is already used' in response.data
    assert not current_user.is_authenticated

    # Try to register a user with the same email as user2
    response = client.post('/register_admin/', data={
        'username': 'user4',
        'email': 'user2@test.com',
        'password': 'password4',
        'checkpassword': 'password4'
    }, follow_redirects=True)
    assert b'This email is already used' in response.data
    assert not current_user.is_authenticated