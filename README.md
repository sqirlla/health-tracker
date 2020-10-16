Health Tracker
===          

This app is intended to be used by organizations who want for their employees to self-report daily temperature, oximeter, and symptom readings for the purpose of determining whether or not that employee will attend work that shift. There is no implication as to what these readings mean or how they will be used, this app is built simply to provide an easy way for these readings to be recorded and managed.     

The basic functions include:    
1. An Admin user can add Users (employees or Admins) to the system - "public" registration is off by default. 
2. Users are prompted to confirm their account and change their password - a dummy password is generated when an Admin adds a User, and it must be changed as it is not recorded anywhere or transmitted to anyone in any way. This prevents Admins from knowing a User's password. 
3. Once a User has a login, they can log in and record their readings. Logins can be done with a username and password or they can log in using their email address and password.
4. A User enters their temperature and oximeter reading in the form of an integer or float with 1 digit of precision. All Users will have an opportunity to record a reading once per day. 
5. The User will determine if they are "working" or "not working" - the system does not decide. The exception is if a User answers in the affirmative to the question regarding symptoms - positive symptoms will disable the "working" button and only allow a "not working" status for that day. 
6. Admins may send reminder emails (from the dashboard) to Users who have not yet recorded a reading and are required to. 
7. Readings may be exported as CSV files, for both all Users and individual Users, and also both including usernames and anonymously. 
8. There are no "delete" functions for Users or readings - not including functions to delete data makes this application "user friendly" in that nothing can be "broken" as a result of user action from the dashboard. Users who will no longer be using the system can be "deactivated" by an Admin from the User view. Deactivation will prevent a User from being allowed to log in. Deactivated Users can be re-activated by an Admin at any point.        

While this app is feature-complete based on the functions named above, there are a few missing features and observed bugs. Please read the Errors & Strange Behaviour as well as the TODO items in this document thouroughly before deploying this app.    

This app is provided under the GNU General Public License v3.0.    
Please see the LICENSE file for details. 

Core
====    

This app runs on [Flask](https://flask.palletsprojects.com/en/1.1.x/), powered by Python 3.8.    
The intended datastore is PostgreSQL, although it is also compatible with sqlite3.    
This app has been designed to run inside a Docker container and without modifications to the Dockerfile will launch using gunicorn.    

[Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/), which is based on [Alembic](https://alembic.sqlalchemy.org/en/latest/) has been included, but not invoked by default. Flask Migrate is a standard way to deal with datastore migrations, so if you believe you will make changes to the data models, you should consider adding the Flask Migrate commands into your deployment flow (flask db init, flask db migrate, flask db upgrade, etc.). If you will not be changing the data models then you can safely ignore this package.     

This app and the included documentation make use of [pipenv](https://pipenv.pypa.io/en/latest/). Opinions on dependency management tools vary, so adjust your setup as preferred. 


Environment    
====    

Running this app requires certain environment variables be in place. Whether you choose to export these values manually prior to execution or you contain them in an `.env` file, the following values must exist:    

```
ORG=[named org]
FLASK_APP=health-tracker.py
FLASK_ENV=[development | production]
DATABASE_URL=[postgresql conn string]
TIMEZONE=[tz definition string]
BOOTSTRAP_EMAIL=[bootstrap admin email]
BOOTSTRAP_PASS=[bootstrap admin password]
BOOTSTRAP_USERNAME=admin
SECURITY_PASSWORD_SALT=[secure string]
ID_SALT=[secure string]
MAIL_SERVER=[your smtp relay address]
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=[smtp relay user]
MAIL_PASSWORD=[smtp relay password]
MAIL_DEFAULT_SENDER=[smtp send as user]
SECURITY_EMAIL_SENDER=[smtp send as user]
SERVER_NAME=[localhost | eventual server address]
TEMP_UNITS_ENCODING=[&#8457; | &#8451;]
```    

Obviously replace `[placeholder]` values with your values where appropriate. 

Temperature Units
====    

This app has no "awareness" for temperature, it treats all temperature readings as a unitless string (collected as a float with one decimal place).    
We attach degrees Fahrenheit or degrees Celsius to the string represenation of the number to provide context in display only. 
The app will default to Fahrenheit if no unit is set via the `TEMP_UNITS_ENCODING` environment variable. Possible options for this variable include: 
`&#8457;` for Fahrenheit and `&#8451;` for Celsius.    

Changing the environment variable will not convert units or affect the values in any way.    


Users (Employees, or other non-priviledged users)
====    

Employees are Users in the system who's role is set to `employee`. All employees must be invited to the system as there is no public registration page turned on by default (I would suggest leaving this setting in place to prevent spam registrations). An admin user must invite employees by using the "Add User" path in the dashboard (found at the bottom of the Users page).    

After an email, username (employee ID), and role have been selected, the user will be added to the system but will not be able to log in as they do not have a password for their account. Upon being created, the system will send an email to the user asking them to click a link which will allow them to reset the password on their account (an unknown, temporary password was generated when the user was created; this password cannot be shown or recovered). Once the password has been reset, the user is instantly logged in and will have access to the dashboard.    

*When an employee (or any role user) is invited and sent an email, the link in that email is only valid for 5 days from the time when the user was created.*    

As of right now, the only actions an "employee" can take are to add new readings and view a selection of their past readings. There are no other functions or features available for this user role. 

Timezones
====    

*This app works with local dates for readings. If you're not sure why times and dates are _very_ hard to deal with then maybe you shouldn't be poking around in the source code. Seriously.*    

When this app is initialized, it will read an ENV var named `TIMEZONE` to determine the local date for all readings. This variable must be set and it must be set according to a standardized list of available time zones. For reference, here is the [list](https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones).    

**We assume that the venue using this application is completely housed within a single timezone, and more specifically that the employees taking readings are also doing so from within the same timezone. If your organization has multiple locations and those locations are in different timezones, it is strongly suggested that you make use of seperate instances of this app, one for each timezone, unless you wish to fork and modify this code.**

While we do use UTC for the timestamp on all new readings, the human side of this app deals with days relative to the location of the establishment where the readings are taking place. While we could certainly record a timezone and offset for each user that takes readings, this will cause problems that are unecessary to deal with. 

What we are doing instead is taking the timestamp, localizing it to the set timezone, and then pulling the YYYY-mm-dd format and storing that for each reading. While this is not an "aware" approach that will let us specify native date types, we can adapt easily by asking for formated strings to run the comparison in our queries. Is this approach OK? Meh, maybe and maybe not. Does it work for what we need it to do? Yes. Be there any more dragons?...    

As of right now (this might change and you should look for the items discussed here to see if this paragraph even applies anymore) we do not take daylight savings time into consideration. Since this app was developed in response to COVID-19, the assumption is this app will be retired before daylight savings time ends. If we were to experience any "spring ahead" or "fall back" issues, they would be more likely to occur during the October fall back period where datetimes could be double counted. This will only affect this app if someone tries to record a reading *during the timechange* which would be between 2 and 3am - something that should be unlikely. The same goes for the March timechange but instead of being double counted the datetime would simply not exist. Is this a giant concern for us? Not really. We'll try and handle the errors by just ignoring the request and not recording the reading. Someone might be upset and report a problem with the app but the admins should know what's happening given the circumstances. *If it is absolutely necessary to record a reading during this time then ask the user to wait an hour and try again.*    
  

In order to give this app a fighting chance in correctly calculating the proper reading date, you will notice that we are also forcefully setting the timezone in our Docker instance to UTC. **Running this app in an environment where the timezone is not set to UTC can give you false readings.** This especially includes local development outside of Docker. So long as the Docker environment is running on UTC and you have set the proper `TIMEZONE` directive in the environment variables, everything should work as expected. You should always test this app in a Docker container and observe the correct date change based on the offset relative to UTC for your intended timezone.    


Emails
====    
This app needs to send email as part of the authentication services used: new user registration, password resets, etc. Since we do not intend to use a local mail proxy (it's 2020, don't set up sendmail on your local server instance) you will more than likely be routing mail through an SMTP relay and that relay is probably Gmail. SMTP relays in Gmail are typically only available in a GSuite (paid) account - free legacy accounts cannot relay mail. After you set up SMTP relay in the admin dashboard, you will need to enable 2FA on the actual account you wish to use as the relay - just a regular user account. After 2FA is set up you can then go to the [App Passwords](https://myaccount.google.com/apppasswords) settings page to create an App Password - you don't want to use the main password for the mail account, that's just not a good idea to throw your mail password around like that.    

Make sure all the values are filled in the `.env` environment variables file (or however you are managing env vars). See the listing above for an example `.env` file. `SECURITY_EMAIL_SENDER` is a required field in order to send emails.    

Custom Email Templates
====    
The `send_mail` function included with `flask_security` is being used to generate an email which is sent to the new user, informing them they need to reset the password on their new account. As this is a non-standard email and a pre-built template is not available, we must provide one. What has been discovered is:   
- The templates must reside in `/app/templates/security/email`
- The template in question must contain both a `.txt` variant and a `.html` variant. 
- Both templates make use of the same context object, which in our case is simply `reset_link`    

Despite what the code in the [`flask_security/utils.py`](https://github.com/mattupstate/flask-security/blob/develop/flask_security/utils.py) says, both template variants must be available. After reading the code you would think that setting the appropriate `EMAIL_PLAINTEXT` or `EMAIL_HTML` config flags would work and simply ignore a template type you do not wish to send, but it appears this is not the case. Both variants must be included.    

Docker    
====    
The application is meant to be run inside a Docker container. After making changes to to the codebase, you must rebuild the container by taking the following steps.     

Freeze requirements:    
`pipenv lock -r > requirements.txt`    

Build the image:    
`docker build -t health-tracker:latest .`    

At this point the image can be saved to any container regitry service you like.    

To run the container:    
`docker run --env-file ./.env -p 5000:5000 -it health-tracker:latest`    

This will start the container in interactive mode.    

Error Reporting    
====    

The default setup for this application will attempt to email the `BOOTSTRAP_EMAIL` address provided should an application error occur (typically 500). This should provide a stacktrace that can be used to deduce the issue.    


Errors & Strange Behaviour
====    

This is a list of known bugs which were either not fixed or not immediately addressed due to how strange they seem or the inconsistentcy of their appearance.    
 
  1. Usernames cannot begin with a number. This seems to be a quirk with flask-security. 
  2. Do not attempt to use passwordless login via flask-security. At one point it was believed that we would turn on passwordless or "magic links" for login, but flask-security will then disbale standard username/password login methods. Passwordless does not offer an alternative login option, it replaces the default option and is the only login sequence available when enabled. 
  3. There is a UNIQUE constraint on username but no handler for a potential duplicate - the application will respond with a general error that the user could not be created.  

TODO
====    
TODO: wire up i18n for multi-language support. Templates already support _() but the core app does not.    


