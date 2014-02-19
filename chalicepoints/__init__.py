import os, sys, string
import json
import hashlib

from flask import Flask, redirect, url_for, abort, jsonify, g
from flask.ext.login import LoginManager, login_user
from flask.ext.openid import OpenID
from google_openid import GoogleOpenID

from flask_peewee.db import Database
from peewee import MySQLDatabase, DoesNotExist

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__, static_folder=os.path.join(PROJECT_ROOT, 'public'),
        static_url_path='/public')

app.config.from_object('chalicepoints.config.DefaultConfig')
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY', app.config['SECRET_KEY'])

if app.config['SECRET_KEY'] is None:
    abort(500)

# Flask-OpenID
open_id = GoogleOpenID()
#open_id = OpenID()
open_id.init_app(app)

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'site.login'
login_manager.init_app(app)

app.config['DATABASE'] = {
    'engine': 'peewee.MySQLDatabase',
    'name': app.config['MYSQL_DATABASE'],
    'user': app.config['MYSQL_USER'],
    'passwd': app.config['MYSQL_PASSWORD'],
    'host': app.config['MYSQL_HOST'],
    'threadlocals': True,
    'autocommit': False
}

db = Database(app)

def register_blueprint(app):
    from chalicepoints.views.site import site
    app.register_blueprint(site)

    from chalicepoints.views.api import api
    app.register_blueprint(api)

register_blueprint(app)

@login_manager.user_loader
def load_user(id):
    from chalicepoints.models.user import User

    try:
        return User.get(User.id == id)
    except:
        return None

@open_id.after_login
def after_login(response):
    from chalicepoints.models.user import User

    email = string.lower(response.email)

    try:
        user = User.get(User.email == email)
        user.url = response.identity_url
        user.save()
    except DoesNotExist:
        user = User()
        user.name = response.fullname
        user.email = email
        user.gravatar = hashlib.md5(email.strip().lower()).hexdigest()
        user.url = response.identity_url
        user.save()

    if not User:
        abort(404)

    login_user(user)
    return redirect(url_for('site.index'))

@app.after_request
def after_request(response):
    if response.status_code < 400:
        db.database.commit()
    else:
        db.database.rollback()

    return response

if __name__ == "__main__":
    port = 9896
    if len(sys.argv) == 2:
        port = int(sys.argv[1])

    app.run(host='0.0.0.0', port=port, debug=True)
