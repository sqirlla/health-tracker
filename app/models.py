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
from app import db
from config import Config
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from sqlalchemy import ForeignKey, desc, text
from sqlalchemy.orm import relationship
import uuid
import re
from datetime import datetime, timedelta, date
import random
import string
from app.utilities import Utilities

roles_users = db.Table('roles_users',
    db.Column('user_id', db.String(), db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), unique=True)
    description = db.Column(db.String())

class Users(db.Model, UserMixin):
    id = db.Column(db.String(), primary_key=True, default=str(uuid.uuid1()))
    email = db.Column(db.String(), unique=True)
    name = db.Column(db.String)
    phone = db.Column(db.String)
    created = db.Column(db.DateTime, index=True)
    username = db.Column(db.String, unique=True, index=True)
    password = db.Column(db.String)
    status = db.Column(db.String)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    readings = db.relationship('Readings', backref=db.backref('users'), order_by=desc(text('Readings.created')))

    def __init__(self, **kwargs):
        super(Users, self).__init__(**kwargs)
        self.id = str(uuid.uuid1())
        self.created = datetime.utcnow()
    
    def reading_today(self):
        """
        reading_today checks to see if the user has satisifed their reading for _today_.
        Today is determined by a comparison for the return value of Utilities.get_date() to get 
        today's current date in our YYYY-mm-dd format and the reading_date value of the very most 
        recent entry in user.readings. 
        If a user does not have any readings, False will be returned. 
        If a user has readings but the most recent doesn't pass the date check, False is 
        returned as we assume they have not yet done a reading for today. 

        Args:
            None
        Returns: 
            bool - True for a reading recorded today, False if no reading for today. 
        """
        if len(self.readings) < 1:
            return False
        else:
            if Utilities.get_date() == self.readings[0].reading_date:
                return True
            else:
                return False
    
    #TODO: update all instances where this method is used to respect that it is staticmethod
    @staticmethod
    def random_password():
        """
        random_password is used to generate a _temporary_ password when creating a new user. 
        This temp password is not transmitted to anyone in any form, it is just used as a placeholder. 
        There is no public registration, users are added by system admins and so we need to fill the password 
        temporarily before the user is allowed to set it to whatever value they want. 
        The user is created and added to the system, they then receive an email which prompts them to change 
        their password. Instead of leaving the password field blank during this step, we fill it in with something 
        temporary. 
        This is obviously not cryptographically secure and should not be used in situations where a secure string is required. 
        We generate a UUID V4 (random ID) and use the first 8 chars, combined with a str generated from a random 12 char 
        sampling of hex chars. This gives us a 21 char random str to use as our temp password. 
        """
        hex_value = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'A', 'B', 'C', 'D', 'E', 'F']
        base = str(uuid.uuid4())
        pass_arr = []
        for _ in range(12):
            pass_arr.append(hex_value[random.randint(0, len(hex_value)-1)])
        return '{}-{}'.format(''.join(pass_arr), base[0:7])

    def normalize_phone(self, input, region='US'):
        """Format a phone number.

        Take a phone-like input and format it to: +12223334455.

        Args:
            input: String, a phone-like string.
            region: String, the 2-letter country code to output the formatted number. Defaults to US. 
        Returns:
            Formatted phone as string.
        """
        if region == 'US':
            fancy_num = re.search(r'^\((?P<area>\d{3})\)\s?(?P<prefix>\d{3})-(?P<subscriber>\d{4})$', input, flags=re.IGNORECASE)
            if fancy_num:
                normalized = '+1' + str(fancy_num.group('area')) + str(fancy_num.group('prefix')) + str(fancy_num.group('subscriber'))
                return normalized
            straight_num = re.search(r'^(?P<number>\d{10})$', input, flags=re.IGNORECASE)
            if straight_num:
                normalized = '+1' + straight_num.group('number')
                return normalized

class Readings(db.Model):
    id = db.Column(db.String(), primary_key=True, default=str(uuid.uuid1()))
    created = db.Column(db.DateTime, index=True)
    reading_date = db.Column(db.String)
    temp = db.Column(db.String)
    oximeter = db.Column(db.String)
    status = db.Column(db.String)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    symptoms = db.Column(db.Boolean) # True == user indicated "symptoms" and system default is Reading == not-working

    def __init__(self, **kwargs):
        super(Readings, self).__init__(**kwargs)
        self.id = str(uuid.uuid1())
        self.created = datetime.utcnow()
        self.reading_date = Utilities.get_date()
        if self.status == True:
            self.status = 'working'
        else:
            self.status = 'not working'
        """We're going to explicitly use 'yes' and 'no' as answers 
        to the symptoms question. This will help to avoid any type casting errors 
        in our logic. 
        A 'yes' means we will 1. set status == 'not working' and 2. set 
        symptoms == True. 
        """
        if self.symptoms == 'yes':
            self.symptoms = True
            self.status = 'not working'

    def get_username(self):
        """
        This could prob be done differently 
        """
        user = Users.query.get(self.user_id)
        return user.username