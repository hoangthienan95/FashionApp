from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LogInForm(FlaskForm):
    username = StringField('username', validators=[Length(3, 20)])
    submit = SubmitField()


class SignUpForm(FlaskForm):
    username = StringField('username', validators=[Length(3, 20)])
    submit = SubmitField()
