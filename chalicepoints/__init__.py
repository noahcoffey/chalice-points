import os, sys, string
import json
import hashlib
import base64

from uuid import uuid4

from flask import Flask, redirect, url_for, abort, jsonify, g, render_template
from flask.ext.login import LoginManager, login_user

from flask_peewee.db import Database
from peewee import MySQLDatabase, DoesNotExist

from chalicepoints.exceptions import APIException, WebException

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__, static_folder=os.path.join(PROJECT_ROOT, 'public'),
        static_url_path='/public')

app.config.from_object('chalicepoints.config.DefaultConfig')
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY', app.config['SECRET_KEY'])

if app.config['SECRET_KEY'] is None:
    abort(500)

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

@login_manager.header_loader
def load_user_from_header(header):
    from chalicepoints.models.user import User

    print header

    if header.startswith('Basic '):
        header = header.replace('Basic ', '', 1)

    print header

    try:
        header = base64.b64decode(header)
    except TypeError:
        pass

    header = header.split(':')[0]

    print header

    try:
        return User.get(User.api_key == header)
    except:
        return None

@app.after_request
def after_request(response):
  if response.status_code < 400:
    db.database.commit()
  else:
    db.database.rollback()

  return response

@app.errorhandler(APIException)
def handle_api_exception(error):
  print 'APIException %s (%d)' % (error.message, error.status_code)
  return jsonify(error=error.message), error.status_code

@app.errorhandler(WebException)
def handle_web_exception(error):
  return render_template('%s.html' % error.status_code, message=error.message), error.status_code

@app.errorhandler(Exception)
def handle_exception(error):
  message = str(error) if app.config['DEBUG'] else 'Sorry, there was an internal server error. Please try again.'
  app.logger.exception(error)
  return jsonify(error=message), 500
