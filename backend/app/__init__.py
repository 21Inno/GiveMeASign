#from app import app
from flask import Flask
#from config import Config

import os, binascii

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = binascii.hexlify(os.urandom(24))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'users.db')  # or 'sqlite:/// + global path to db
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.config.from_object(Config)

from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.login_message = "You can not access this page. Please log in to access this page."
login_manager.session_protection = "strong"

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

#import app.routes
from . import routes
