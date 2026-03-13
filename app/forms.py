# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User
import sqlalchemy as sa
from app import db
from datetime import date


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About Me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')


class ExclusionForm(FlaskForm):
    excluded_email = StringField(
        'Welcher Benutzer soll exkludiert werden (E-Mail)',
        validators=[DataRequired(), Email()]
    )

    policy = SelectField(
        'Von welcher Policy soll exkludiert werden?',
        coerce=int,
        choices=[],
        validators=[DataRequired()]
    )

    until = DateField(
        'Bis wann',
        validators=[DataRequired()],
        format='%Y-%m-%d'
    )

    submit = SubmitField('Zur Exclusion-Liste hinzufügen')
    load_db = SubmitField('Datenbank auslesen')

    def validate_until(self, field):
        if field.data < date.today():
            raise ValidationError('Das Datum muss heute oder in der Zukunft liegen.')