from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LogInForm(FlaskForm):
    username = StringField('Username', validators=[Length(3, 20, message='Length must be between 3 and 20.')])
    submit = SubmitField('Log In')


class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[Length(3, 20, message='Length must be between 3 and 20.')])
    submit = SubmitField('Sign Up')
