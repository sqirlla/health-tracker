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
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from app import db
from flask import render_template, flash, redirect, url_for, Response, request, g
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, current_user, url_for_security
from flask_security.utils import encrypt_password, verify_password, hash_password, login_user, send_mail
from flask_security.decorators import roles_required, roles_accepted
from app.models import Users, Readings, Role
from app.forms import ReadingsForm, AddUser
import os
from datetime import datetime
from config import Config
from app import mail
from flask_security.recoverable import generate_reset_password_token
from app.utilities import Utilities
import traceback

basedir = os.path.abspath(os.path.dirname(__file__))
user_datastore = SQLAlchemyUserDatastore(db, Users, Role)
security = Security(app, user_datastore)

@app.context_processor
def inject_org():
    """Inject the org variable into our templates
    as it is commonly used
    """
    if Config.ORG:
        return dict(org=Config.ORG)
    else:
        return dict(org=None)

@app.context_processor
def inject_units():
    """Inject the units variable into our templates
    as it is commonly used. If config var isn't set 
    (it really always should be), default to F
    """
    if Config.TEMP_UNITS_ENCODING:
        return dict(units=Config.TEMP_UNITS_ENCODING)
    else:
        return dict(units="&#8457;")


@app.before_first_request
def bootstrap():
    """
    bootstrap will handle the creation of our user roles and admin 
    user setup when the app is first run. 
    This func will not be run until a request is made; it does not run 
    when the app is invoked. 
    Typically just loading the home or login page will be enough to run 
    bootstrap, but do not expect roles and admin user to exist before you 
    have requested at least one page. 
    It should go without saying that the admin user should immediately reset their 
    password once registered. Just follow the reset password flow from the link on the login page. 
    
    *Should you lose the admin login credentials and you cannot recover from a password reset*
    You will need to manually go into your datastore and identify the id of the admin user. 
    Once you have that id, you will need to remove any associated readings and then also delete the 
    roles_users entry where userid = user.id of your admin. 
    Once readings and the roles_users entries have been removed, you can then delete the admin user 
    from the datastore. 
    Once deleted, stop and then restart the application and load a page to kick off the bootstrap func again. 
    Your admin user will be restored to the initial state, using the password defined in the BOOTSTRAP_PASS env var. 
    The admin user has no ownership over anything other than their own readings, so there is no danger in 
    removing and re-adding this user, other than the fact that you will lose their readings, if they have any.
    """
    db.create_all()
    admin = user_datastore.find_role('admin')
    if not admin:
        user_datastore.create_role(name='admin', description='admin user role')
        db.session.commit()
        admin = user_datastore.find_role('admin')
    employee = user_datastore.find_role('employee')
    if not employee:
        user_datastore.create_role(name='employee', description='employee user role')
        db.session.commit()
    admin_user = user_datastore.find_user(email=Config.BOOTSTRAP_EMAIL)
    if not admin_user:
        user_datastore.create_user(email=Config.BOOTSTRAP_EMAIL, username=Config.BOOTSTRAP_USERNAME, password=hash_password(Config.BOOTSTRAP_PASS))
        db.session.commit()
        admin_user = user_datastore.find_user(email=Config.BOOTSTRAP_EMAIL)
        user_datastore.add_role_to_user(admin_user, admin)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    """
    These items are explicitly stated for clarity. 
    TODO: make use of the methods and objects available by default in jinja to clean up this template.
    """
    user = current_user
    today = Utilities.get_date()
    is_admin = False
    all_users = []
    if user.has_role('admin'):
        is_admin = True
        all_users = Users.query.all()
    return render_template('home.html', user=user, is_admin=is_admin, users=all_users, today=today)

@app.route('/readings', methods=['GET'])
@login_required
@roles_required('admin')
def readings():
    """
    A paginated view of all readings, sorted in desc order. 
    """
    page = request.args.get("page", 1, type=int)
    readings = Readings.query.order_by(Readings.created.desc()).paginate(page, Config.POSTS_PER_PAGE, True)
    next_url = url_for('readings', page=readings.next_num) if readings.has_next else None
    prev_url = url_for('readings', page=readings.prev_num) if readings.has_prev else None
    return render_template('all_readings.html', readings=readings.items, next=next_url, prev=prev_url)

@app.route('/readings/new', methods=['GET', 'POST'])
@login_required
def new_reading():
    """
    Record a new reading. 
    This is available to both admins and employees.
    Before taking a reading we will check the most recent user's reading and compare that 
    to "today" in order to see if a reading is required. 
    No date math or time deltas, just str comparison via Users.reading_today()
    """
    user = current_user
    form = ReadingsForm()
    if user.reading_today():
        return render_template('reading_exists.html')
    if form.validate_on_submit():
        try:
            reading = Readings(user_id=user.id, temp=str(form.temp.data), oximeter=str(form.oximeter.data), status=form.working_btn.data, symptoms=form.symptoms.data)
            db.session.add(reading)
            db.session.commit()
            flash('Your reading has been recorded', category='success')
            return redirect(url_for('single_reading', id=reading.id))
        except Exception as e:
            flash('Your reading could not be recorded, please try again. If this problem continues, please inform your manager.', category='error')
            app.logger.debug(f'Reading err: {datetime.now()} \n {e}')
            return redirect(url_for('new_reading'))
    return render_template('new_reading.html', form=form)

@app.route('/readings/<id>', methods=['GET'])
@login_required
def single_reading(id):
    """
    Single view of a reading, really only shown after a reading has been recorded. 
    TODO: change the template name to something more appropriate.
    """
    reading = Readings.query.get(id)
    return render_template('reading_accepted.html', reading=reading)


@app.route('/users', methods=['GET'])
@login_required
@roles_accepted('admin')
def users():
    """
    Simple view of all users. 
    """
    users = Users.query.all()
    return render_template('all_users.html', users=users)

@app.route('/users/<id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def single_user(id):
    """
    View of single user. 
    """
    user = Users.query.get(id)
    return render_template('single_user.html', user=user)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
@roles_accepted('admin')
def new_user():
    """
    new_user is a route used exclusively by system admins to add new users to the system. 
    There is no public registration page for this application (per the flask-security settings), 
    users must be added by an admin. 
    We will prompt for an email, username, and role, then create the user and send an email 
    informing them that they have been added to the system and must change their password. 
    The change password step is required as the temp password we generated for them is never 
    revealed, just hashed and stored to protect the account from un-authorized logins while the 
    confirmation process plays out. 
    """
    form = AddUser()
    if form.validate_on_submit():
        new_user = user_datastore.find_user(email=form.email.data)
        if new_user:
            flash('User with given email address already exists. User not created.', category='error')
            return redirect(url_for('new_user'))
        
        """
        Try and create the new user with given email, username, and role. 
        Assign them a temp password. 
        Users should be activated by default but for some reason we needed to 
        manually activate. 
        """
        try:
            new_user = user_datastore.create_user(email=form.email.data, username=form.username.data, password=hash_password(Users.random_password()))
            role = user_datastore.find_role(form.roles.data)
            user_datastore.add_role_to_user(new_user, role)
            user_datastore.activate_user(new_user)
            db.session.commit()
        except Exception as e:
            app.logger.debug(e)
            db.session.rollback()
            flash('There was an error creating this user. Please try again before reporting.', category='error')
            return redirect(url_for('new_user'))
        
        """
        Now that we have a new user, we're going to try and send them their "activation" link via email. 
        We're really just making use of the built-in password reset function, so generate a new reset token 
        and send the mail via the flask-security send_mail func. 
        This sequence makes use of a custom email template.
        """
        try:
            link = url_for_security('reset_password', token=generate_reset_password_token(new_user), _external=True)
            subject = 'Activate your account for the Health Tracker'
            
            if Config.ORG:
                subject = f'Activate your account for the {Config.ORG} Health Tracker'
            send_mail(subject, new_user.email, 'invite_new_user', reset_link=link)
        except Exception as e:
            db.session.rollback()
            flash('New user was created but invitation email was not sent.', category='error')
            return redirect(url_for('new_user'))
        
        flash(f'New user "{new_user.username}" was created and invitation email sent.', category='success')
        return redirect(url_for('new_user'))
    return render_template('new_user.html', form=form)

@app.route('/api/readings', methods=['GET'])
@login_required
@roles_required('admin')
def api_readings():
    """
    This route returns a csv file of all readings, grouped by reading date. 
    The default is to include all relevant columns in the csv, which includes username. 
    An alternate version of this report can be obtained by appending ?anon=true to the end of the URL. 
    This "anonymous" csv will have the usernames stripped out.
    """
    filename = "all_readings-{}.csv".format(Utilities.get_date())
    header_cols = ('id', 'created', 'temp', 'oximeter', 'symptoms', 'reading_date', 'status', 'username')
    if request.args.get('anon') == 'true':
        filename = "all_readings_anon-{}.csv".format(Utilities.get_date())
        header_cols = ('id', 'created', 'temp', 'oximeter', 'symptoms', 'reading_date', 'status')
    readings = Readings.query.order_by(Readings.created.desc()).all()
    response = Response(Utilities.stream_generate_readings(header_cols, readings), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename=filename)
    return response

@app.route('/api/readings/<user_id>', methods=['GET'])
@login_required
@roles_required('admin')
def api_readings_user(user_id):
    """
    This route returns a csv file of all readings for a particular user, grouped by reading date. 
    The default is to include all relevant columns in the csv, which includes username. 
    An alternate version of this report can be obtained by appending ?anon=true to the end of the URL. 
    This "anonymous" csv will have the usernames stripped out.
    """
    user = Users.query.get(user_id)
    readings = user.readings
    filename = "{}_readings-{}.csv".format(user.username, Utilities.get_date())
    header_cols = ('id', 'created', 'temp', 'oximeter', 'symptoms', 'reading_date', 'status')
    if request.args.get('anon') == 'true':
        filename = "anon_user_{}_readings-{}.csv".format(user.id, Utilities.get_date())
        header_cols = ('created', 'temp', 'oximeter', 'symptoms', 'reading_date', 'status')
    response = Response(Utilities.stream_generate_readings(header_cols, readings), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename=filename)
    return response

@app.route('/users/<user_id>/reminder', methods=['POST'])
@login_required
@roles_required('admin')
def send_reminder(user_id):
    """
    Should an admin see that a particular employee has not yet provided a reading, the admin may 
    prompt the user for a reading via email. 
    This route will attempt to send a reminder email to the user in question. 
    We make use of the flask-security send_mail function and are providing a custom email template. 
    """
    try:
        user = Users.query.get(user_id)
        send_mail('You are required to record health readings', user.email, 'send_reminder', link=url_for('new_reading', _external=True))
        flash(f'Reminder email sent to { user.email }', category='success')
    except Exception as e:
        flash(f'Reminder email was not sent to { user.email }, there was an error. ', category='error')
    
    if request.args.get('return'):
        return redirect(request.args.get('return'))
    else:
        return redirect(url_for('home'))

@app.route('/users/<user_id>/invitation', methods=['POST'])
@login_required
@roles_required('admin')
def resend_invitation(user_id):
    """
    For the purpose of re-sending a lost "activation" email, this endpoint allows 
    an admin to re-send that message. 
    This is a convenience option in the admin's dashboard (on the individual user's profile) but it 
    is no different than the reset password flow. We simply generate a reset password token and send the 
    email using our "invite" custom template. 
    Something to note: You can instruct your users who might have misplaced their "activation" email to just 
    use the password reset link from the login page. It's the same flow and they can request a new password 
    with their email address. 
    """
    user = Users.query.get(user_id)
    try:
        link = url_for_security('reset_password', token=generate_reset_password_token(user), _external=True)
        subject = 'Activate your account for the Health Tracker'
        if Config.ORG:
            subject = f'Activate your account for the {Config.ORG} Health Tracker'
        send_mail(subject, user.email, 'invite_new_user', reset_link=link)
        flash('User invitation email was sent.', category='success')
    except Exception as e:
        app.logger.debug(e)
        db.session.rollback()
        flash('User invitation email was not sent, there was an error', category='error')
    return redirect(url_for('single_user', id=user_id))

@app.route('/users/<user_id>/deactivate', methods=['POST'])
@login_required
@roles_required('admin')
def deactivate_user(user_id):
    """
    Users in the system cannot be deleted, but their account can be deactivated. 
    Deactivation means the user can no longer log in.  
    """
    user_model = Users.query.get(user_id)
    """How dumb would that be if we let an admin 
    deactivate their own account? Let's not do that.
    """
    if user_model == current_user:
        flash('You cannot deactivate your own account.', category='error')
        return redirect(url_for('home'))
    try:
        result = user_datastore.deactivate_user(user_model)
        db.session.commit()
        if result:
            flash(f'User { user_model.email } has been deactivated.', category='success')
        else:
            raise Exception
    except Exception as e:
        app.logger.debug("Error in deactivating user - user_datastore.deactivate_user raised an exception")
        flash(f'Error: could not be deactivated. ', category='error')
    
    if request.args.get('return'):
        return redirect(request.args.get('return'))
    else:
        return redirect(url_for('home'))

@app.route('/users/<user_id>/activate', methods=['POST'])
@login_required
@roles_required('admin')
def activate_user(user_id):
    """
    Activate a de-activated user. 
    This can restore a user's account or fix an issue if the account was not 
    properly activated on creation.  
    """
    try:
        user_model = Users.query.get(user_id)
        
        result = user_datastore.activate_user(user_model)
        db.session.commit()
        if result:
            flash(f'User { user_model.email } has been activated.', category='success')
        else:
            raise Exception
    except Exception as e:
        app.logger.debug("Error in activating user - user_datastore.activate_user raised an exception")
        flash(f'Error: could not be activated. ', category='error')
    
    if request.args.get('return'):
        return redirect(request.args.get('return'))
    else:
        return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def system_err(e):
    """
    We're not anticipating full-blown monitoring in the context of running this 
    app, so in the interest of alerting if a 500 err is encountered, we're going 
    to attempt to email the admin with the details of err. 
    """
    try:
        send_mail('The Health Tracker system encountered an error', Config.BOOTSTRAP_EMAIL, 'system_500_email', error=traceback.format_exc())
    except Exception as ex:
        """I mean, if this exception is raised, you got problems"""
        app.logger.debug(ex)
    return render_template('500.html'), 500