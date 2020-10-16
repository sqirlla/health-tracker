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
import os
from dotenv import load_dotenv
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    """Many of the configuration variables here are populated through the use of 
    environment variables, either set via an export prior to app boot or imported 
    through a .env file. 
    Variables which are not set via env vars have been defaulted to either a required 
    value or a sensible default for the context of this app. 
    Many of the vars set here can be traced back to one of the following packages: 
    [flask](https://flask.palletsprojects.com/en/1.1.x/)
    [flask-sqlalchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/)
    [flask-security](https://pythonhosted.org/Flask-Security/)
    """
    ENV = os.environ.get('FLASK_ENV')
    ORG = os.environ.get('ORG')
    APP_BASE_URL = os.environ.get('APP_BASE_URL')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'who wants to know'
    TIMEZONE = os.environ.get('TIMEZONE')
    BOOTSTRAP_EMAIL = os.environ.get('BOOTSTRAP_EMAIL')
    BOOTSTRAP_PASS = os.environ.get('BOOTSTRAP_PASS')
    BOOTSTRAP_USERNAME = os.environ.get('BOOTSTRAP_USERNAME')
    SECURITY_POST_LOGIN_VIEW = '/home'
    SECURITY_CHANGEABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL = True
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = True
    ID_SALT=os.environ.get('ID_SALT')
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT')
    BOOTSTRAP_SERVE_LOCAL = True
    SECURITY_USER_IDENTITY_ATTRIBUTES=['email', 'username']
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    SECURITY_EMAIL_SENDER = os.environ.get('SECURITY_EMAIL_SENDER')
    EMAIL_PLAINTEXT = True
    EMAIL_HTML = False
    TEMP_UNITS_ENCODING = os.environ.get('TEMP_UNITS_ENCODING') or '&#8457;'
    POSTS_PER_PAGE = 1