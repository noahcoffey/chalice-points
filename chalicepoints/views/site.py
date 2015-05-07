import os, sys, string
import hashlib
import urllib, urllib2
import httplib2
import json

from base64 import b64encode
from time import time
from uuid import uuid4

from flask import Flask, request, redirect, url_for, \
    abort, render_template, jsonify, send_from_directory, \
    Response, g, Blueprint, current_app, session

from flask.ext.login import login_required, current_user, logout_user, login_user
from oauth2client.client import OAuth2WebServerFlow

import chalicepoints
from chalicepoints import login_manager
from chalicepoints.models.user import User

from peewee import DoesNotExist

site = Blueprint('site', __name__)

@site.route('/login')
def login():
  csrf_token = b64encode(os.urandom(24))
  session['csrf_token'] = csrf_token

  flow = OAuth2WebServerFlow(
    client_id=current_app.config['GOOGLE_API_CLIENT_ID'],
    client_secret=current_app.config['GOOGLE_API_CLIENT_SECRET'],
    scope=current_app.config['GOOGLE_API_SCOPE'],
    redirect_uri=current_app.config['SITE_URL'] + '/auth'
  )

  auth_url = '%s&state=%s' % (flow.step1_get_authorize_url(), csrf_token)
  return redirect(auth_url)

@site.route('/auth')
def auth():
  session_csrf_token = session.pop('csrf_token', None)
  csrf_token = request.args.get('state', None)
  code = request.args.get('code')

  if not session_csrf_token or not csrf_token:
    abort(400)

  if not code:
    abort(400)

  if csrf_token != session_csrf_token:
    abort(400)

  flow = OAuth2WebServerFlow(
    client_id=current_app.config['GOOGLE_API_CLIENT_ID'],
    client_secret=current_app.config['GOOGLE_API_CLIENT_SECRET'],
    scope=current_app.config['GOOGLE_API_SCOPE'],
    redirect_uri=current_app.config['SITE_URL'] + '/auth'
  )

  credentials = flow.step2_exchange(code)

  http = credentials.authorize(httplib2.Http())

  id_token = credentials.id_token
  if not validate_id_token(id_token):
    abort(400)

  (headers, content) = http.request('https://www.googleapis.com/oauth2/v3/userinfo', 'GET')

  if headers['status'] != '200':
    abort(500)

  try:
    userinfo = json.loads(content)
  except ValueError:
    abort(500)

  email = string.lower(userinfo['email'])

  try:
    user = User.get(User.email == email)
    user.name = userinfo['name']
    user.save()
  except DoesNotExist:
    user = User()
    user.name=userinfo['name']
    user.email=email
    user.api_key=str(uuid4())
    user.gravatar=hashlib.md5(email.strip().lower()).hexdigest()
    user.url = id_token['sub']
    user.save()

  if not user:
    abort(500)

  login_user(user)

  return redirect(url_for('site.index'))

def validate_id_token(id_token):
  if not id_token:
    return False

  if isinstance(id_token['aud'], list):
    if current_app.config['GOOGLE_API_CLIENT_ID'] not in id_token['aud']:
      return False

    if 'azp' not in id_token:
      return False
  else:
    if current_app.config['GOOGLE_API_CLIENT_ID'] != id_token['aud']:
      return False

  if 'azp' in id_token and id_token['azp'] != current_app.config['GOOGLE_API_CLIENT_ID']:
    return False

  if not (id_token['iat'] <= time() < id_token['exp']):
    return False

  if 'GOOGLE_DOMAIN' in current_app.config:
    if 'hd' not in id_token or id_token['hd'] != current_app.config['GOOGLE_DOMAIN']:
      return False

  return True

@site.route('/logout')
def logout():
  logout_user()
  return redirect(url_for('site.index'))

@site.route('/humans.txt')
def humans():
    return send_from_directory(os.path.join(current_app.root_path, 'public'),
        'humans.txt', mimetype='text/plain')

@site.route('/robots.txt')
def robots():
    return send_from_directory(os.path.join(current_app.root_path, 'public'),
        'robots.txt', mimetype='text/plain')

@site.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'public'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')

@site.route('/', defaults={'path': 'index'})
@site.route('/<path:path>')
@login_required
def index(path):
    return render_template('index.html',
        user_json=current_user.to_json(for_public=True))
