"""
The Health Tracker application is an easy way for organizations to record and 
manage the daily vital readings of their employees, partners, contractors, etc. 
in response to the COVID-19 pandemic. 

Copyright (C) 2020 Sqirl, LLC

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Please refer to LICENSE in the project repository for details.
"""
from app import app
from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, TextAreaField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, Length, Regexp, Optional, NumberRange
from wtforms.fields.html5 import TelField, DateField, DecimalField
from app.models import Users, Role
import re

def get_roles():
    try:
        roles = Role.query.all()
        choose = 'Choose...'
        container = [('', choose)]
        for role in roles:
            container.append((role.name, role.name))
        return container
    except Exception as e:
        return [('error', 'error')]

def decimal_validation(form, field):
    pattern = re.compile('^\d{2,3}(\.\d{1})?$')
    if not pattern.fullmatch(str(field.data)):
        raise ValidationError('Must be a 2-3 digit number with 0 or 1 decimal place')

class ReadingsForm(FlaskForm):
    temp = DecimalField('Temperature', validators=[DataRequired(message='This field is required'), decimal_validation])
    oximeter = DecimalField('Oximeter', validators=[DataRequired(message='This field is required'), decimal_validation])
    symptoms = BooleanField('Are you experiencing COVID-19 symptoms?', validators=[])
    working_btn = SubmitField("I'm Working")
    not_working_btn = SubmitField("I'm Going Home")

class AddUser(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message='This field is required'), Email(message='A valid email address is required.')])
    username = StringField('Username', validators=[DataRequired(message='This field is required')])
    roles = SelectField('Role', choices=get_roles())
    submit = SubmitField("Add")