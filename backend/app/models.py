from . import app
from . import db
from . import login_manager
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash


def sign_to_dict(sign):
    sign_dict = {}
    sign_dict['id'] = sign.id
    sign_dict['mot'] = sign.mot
    sign_dict['gloss'] = sign.gloss
    sign_dict['keywords'] = sign.keywords
    sign_dict['url'] = sign.url
    sign_dict['datetime'] = sign.datetime.strftime('%Y-%m-%d %H:%M:%S')

    return sign_dict


def prop_to_dict(sign):
    prop_dict = {}
    prop_dict['id'] = sign.id
    prop_dict['gloss'] = sign.gloss
    prop_dict['keywords'] = sign.keywords
    prop_dict['url'] = sign.url
    prop_dict['author'] = sign.author_name
    prop_dict['group_name'] = sign.group_name
    prop_dict['certified'] = sign.certified

    return prop_dict


class Person(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    role = db.Column(db.Enum('admin', 'normal'), nullable=False, default='normal')

    __mapper_args__ = {
        'polymorphic_on': role,
    }


class Admin(Person):
    id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(20))
    password_hash = db.Column(db.String(100))
    groups = db.relationship('Group', backref='admin', lazy=True)
    __mapper_args__ = {
        'polymorphic_identity': 'admin'
    }

    def __repr__(self):
        return "< Admin >" + self.username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(20))
    password_hash = db.Column(db.String(100))
    description = db.Column(db.String(2000), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    # group_prop = relationship('SignProposition', backref='group', lazy=True)

    users = db.relationship('User', backref='group', lazy=True)

    def __repr__(self):
        return "< Group >" + self.name

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class User(Person):
    id = db.Column(db.Integer, db.ForeignKey('person.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    history = relationship('UserHistory', backref='user', lazy=True)
    # user_prop = relationship('SignProposition', backref='user', lazy=True)

    blocked = db.Column(db.Boolean, unique=False, nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'normal'
    }


class UserHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'))
    sign_id = db.Column(db.Integer, ForeignKey('sign_history.id'))


class SignHistory(db.Model):
    __tablename__ = 'sign_history'
    id = db.Column(db.Integer, primary_key=True)
    mot= db.Column(db.String(128))
    gloss = db.Column(db.String(128))
    keywords = db.Column(db.String(500))
    url = db.Column(db.String(1000))
    datetime = db.Column(db.DateTime, default=datetime.now)
    user_history = relationship('UserHistory', backref='sign_history', lazy=True)

    def __str__(self):
        return f"Sign {self.id}: {self.gloss}, {self.keywords} "


class SignProposition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gloss = db.Column(db.String(128))
    keywords = db.Column(db.String(500))
    url = db.Column(db.String(1000))
    author_name = db.Column(db.String(128))  # db.Column(db.Integer, ForeignKey('user.username'))
    group_name = db.Column(db.String(128))  # db.Column(db.Integer, ForeignKey('group.name'))
    certified = db.Column(db.Enum('False', 'True', 'waiting'), nullable=False, default='waiting')

    def __str__(self):
        return f"Sign {self.id}: {self.gloss}, {self.keywords} "
    

""" Table used to handle Password Reset asked by an Admin. The user receives an email with a link to change his PW """
class PWReset(db.Model):
    __tablename__ = "pwreset"
    id = db.Column(db.Integer, primary_key=True)
    reset_key = db.Column(db.String(128), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    datetime = db.Column(db.DateTime(timezone=True), default=datetime.now)
    user = db.relationship(Admin, lazy='joined')
    has_activated = db.Column(db.Boolean, default=False)


with app.app_context():
    db.drop_all()
    db.create_all()

    # admin
    admin0 = Admin(email='admin@example.com', username='StMarie_admin', role='admin')
    admin0.set_password('azerty')
    admin1 = Admin(email='public@example.com', username='Public_admin', role='admin')
    admin1.set_password('public')
    # create a new group
    group_StMarie = Group(name="StMarie", admin=admin0)
    group_StMarie.set_password("StMarie")
    group_Public = Group(name="Public", password="Public", admin=admin1)
    group_Public.set_password("Public")
    # create a new user and add them to the group
    new_user = User(username='StMarie_inno', role="normal", group=group_StMarie, blocked=False)
    new_user1 = User(username='StMarie_baba', role="normal", group=group_StMarie, blocked=False)
    anonyme_user = User(username='anonyme', role="normal", group=group_Public, blocked=False)

    now = datetime.now()

    print("now =", now)

    # dd/mm/YY H:M:S
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)

    # create a new sign
    new_sign = SignHistory(mot="alimentation",gloss='MANGER', keywords='manger, alimentation, dessert',
                    url='https://corpus-lsfb.be/img/pictures/signe_dbdb6f59d8edcdc7d51135d3f6f62dd4.gif', datetime=now)
    new_sign1 = SignHistory(mot="sommeil", gloss='DORMIR', keywords='dormir, dormeur, sommeil',
                     url='https://corpus-lsfb.be/img/pictures/signe_aba4817ea7264d451f611a084563b910.gif', datetime=now)
    new_sign2 = SignHistory(mot="cours", gloss='COURIR', keywords='courir, course',
                     url='https://corpus-lsfb.be/img/pictures/signe_29457ccb6c819c48e83c53aa4e882c62.gif', datetime=now)

    # create a new user history and associate it with the user and the sign
    new_user_history = UserHistory(user=new_user, sign_history=new_sign)
    new_user_history1 = UserHistory(user=new_user, sign_history=new_sign1)
    new_user_history2 = UserHistory(user=new_user1, sign_history=new_sign2)

    # proposition
    proposition = SignProposition(gloss="Lièvres_0", keywords="lièvre, lièvres",
                                  url="https://www.gifsanimes.com/data/media/1246/lievre-image-animee-0001.gif",
                                  author_name=new_user.username, group_name=group_StMarie.name, certified= 'waiting')
    proposition1 = SignProposition(gloss="Lièvres_0", keywords="lièvre, lièvres",
                                   url="https://www.gifsanimes.com/data/media/1246/lievre-image-animee-0012.gif",
                                   author_name=anonyme_user.username, group_name=group_Public.name, certified= 'waiting')

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
    print(new_user.username)
    print(new_user.group.name)
    print(new_user.history)
    print(new_user.group.admin_id)
    print(admin0.id, admin0.username)


@login_manager.user_loader
def user_loader(userid):
    user = Person.query.get(int(userid))
    """if not user:
        user = User.query.get(int(userid))"""
    return user
