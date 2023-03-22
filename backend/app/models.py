from . import app
from . import db
from . import login_manager
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


def sign_to_dict(sign):
    sign_dict = {}
    # sign_dict['id'] = sign.id
    sign_dict['gloss'] = sign.gloss
    sign_dict['keywords'] = sign.keywords
    sign_dict['url'] = sign.url
    sign_dict['datetime'] = sign.datetime.strftime('%Y-%m-%d %H:%M:%S')
    return sign_dict


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    role = db.Column(db.Enum('admin', 'normal'), nullable=True)
    group_id = db.Column(db.Integer, ForeignKey('group.id'))
    history = relationship('UserHistory', backref='user', lazy=True)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(128))
    users = relationship('User', backref='group', lazy=True)

    def __repr__(self):
        return "< Group >" + self.name

    def set_password(self, password):
        self.password = password

    def check_password(self, password1):
        return self.password == password1


class UserHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'))
    sign_id = db.Column(db.Integer, ForeignKey('sign.id'))


class Sign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gloss = db.Column(db.String(128))
    keywords = db.Column(db.String(500))
    url = db.Column(db.String(1000))
    datetime = db.Column(db.DateTime, default=datetime.utcnow)
    user_history = relationship('UserHistory', backref='sign', lazy=True)

    def __str__(self):
        return f"Sign {self.id}: {self.gloss}, {self.keywords} "


class SignProposition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gloss = db.Column(db.String(128))
    keywords = db.Column(db.String(500))
    url = db.Column(db.String(1000))
    author_name = db.Column(db.String(128))
    group_name = db.Column(db.String(128))

    def __str__(self):
        return f"Sign {self.id}: {self.gloss}, {self.keywords} "


with app.app_context():
    db.drop_all()
    db.create_all()

    # create a new group
    group_StMarie = Group(name="StMarie", password="StMarie")
    group_Public = Group(name="Public", password="Public")
    # create a new user and add them to the group
    new_user = User(username='inno', role='normal', group=group_StMarie)
    new_user1 = User(username='baba', role='normal', group=group_StMarie)
    anonyme_user = User(username='ano', role='normal', group=group_Public)
    # create a new sign
    new_sign = Sign(gloss='MANGER', keywords='manger, alimentation, dessert',
                    url='https://corpus-lsfb.be/img/pictures/signe_dbdb6f59d8edcdc7d51135d3f6f62dd4.gif')
    new_sign1 = Sign(gloss='DORMIR', keywords='dormir, dormeur, sommeil',
                     url='https://corpus-lsfb.be/img/pictures/signe_aba4817ea7264d451f611a084563b910.gif')
    new_sign2 = Sign(gloss='COURIR', keywords='courir, course',
                     url='https://corpus-lsfb.be/img/pictures/signe_29457ccb6c819c48e83c53aa4e882c62.gif')

    # create a new user history and associate it with the user and the sign
    new_user_history = UserHistory(user=new_user, sign=new_sign)
    new_user_history1 = UserHistory(user=new_user, sign=new_sign1)
    new_user_history2 = UserHistory(user=new_user1, sign=new_sign2)

    #proposition
    proposition = SignProposition(gloss="Lievres_0",keywords="lievre, lievres",url="app/static/videos/StMarie/videos_Lievres/Lievres_0.mp4",author_name=new_user.username,group_name=group_StMarie.name)
    proposition1 = SignProposition(gloss="Lievres_0",keywords="lievre, lievres",url="app/static/videos/StMarie/videos_Lievres/Lievres_0.mp4",author_name=anonyme_user.username, group_name=group_Public.name)

    # add the group, user, sign, and user history to the database
    db.session.add(group_StMarie)
    db.session.add(new_user)
    db.session.add(new_user1)
    db.session.add(anonyme_user)
    db.session.add(new_sign)
    db.session.add(new_sign1)
    db.session.add(new_sign2)
    db.session.add(new_user_history)
    db.session.add(new_user_history1)
    db.session.add(new_user_history2)
    db.session.add(proposition)
    db.session.add(proposition1)
    db.session.commit()

    # print the user's id and their associated group and history
    print(new_user.id)
    print(new_user.group.name)
    print(new_user.history)
    """for hist in new_user.history:
        print(hist.sign_id)
        sign = Sign.query.filter_by(id = hist.sign_id).first()
        print(sign_to_dict(sign))"""


@login_manager.user_loader
def user_loader(userid):
    return User.query.get(int(userid))
