from . import app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField
from wtforms.widgets import TextArea
from wtforms.validators import InputRequired, DataRequired, Length, NoneOf, EqualTo, Email
from .models import User, Admin

# Form for enter a login
class LoginAdminForm(FlaskForm):
    username = StringField("Username:", validators=[InputRequired(), DataRequired(), Length(min=2, max=20)])
    password = PasswordField("Password:", validators=[InputRequired(), DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Submit')

    
# Form for register
class RegisterAdminForm(FlaskForm):
    with app.app_context():
        users = [u.username for u in Admin.query.all()]
        emails = [u.email for u in Admin.query.all()]
    username = StringField("Username:", validators=[InputRequired(), DataRequired(), Length(min=2, max=20,message="Between 2 and 20 characters"),NoneOf(values=users,message="This username is already used")])
    email = StringField('Email', validators=[InputRequired(),DataRequired(), Email(), Length(min=6, max=50),NoneOf(values=emails,message="This email is already used")])
    password = PasswordField("Mot de passe:", validators=[InputRequired(), DataRequired(), Length(min=2, max=20,message="Between 2 and 20 characters"),EqualTo("checkpassword", message="Passwords must match")])
    checkpassword = PasswordField("Confirme Mot de passe:", validators=[InputRequired(), DataRequired(), Length(min=2, max=20),])
    submit = SubmitField('Submit')


# Form for enter a task
class GroupeForm(FlaskForm):
    name = StringField("Nom du groupe:", validators=[InputRequired(), Length(min=2, max=20, message="Between 2 and 20 characters")])
    description = StringField("Description :", widget=TextArea())
    password = PasswordField("Mot de passe:", validators=[InputRequired(), DataRequired(), Length(min=2, max=20,message="Between 2 and 20 characters"),EqualTo("checkpassword", message="Passwords must match")])
    checkpassword = PasswordField("Confirme Mot de passe:", validators=[InputRequired(), DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Submit')
