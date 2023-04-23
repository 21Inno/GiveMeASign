import sys
sys.path.append('../')

from flask_login import current_user
from app import app
from app.models import Group, User

def test_login():
    with app.test_client() as client:
        # Test avec des informations de connexion invalides
        response = client.post('/login/', data=dict(
            group='Invalid group',
            username='Invalid user',
            password='Invalid password'
        ))
        assert response.status_code == 302
        assert response.location.endswith('/login')

        # Créer un groupe et un utilisateur valide pour le test
        group = Group(name='Test Group')
        group.set_password('testpassword')
        user = User(username='testuser', role='normal', group=group, blocked=False)
        app.db.session.add(group)
        app.db.session.add(user)
        app.db.session.commit()

        # Test avec des informations de connexion valides
        response = client.post('/login/', data=dict(
            group='Test Group',
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)
        assert response.status_code == 200
        assert current_user.username == 'Test Group_testuser'
        assert current_user.role == 'normal'
