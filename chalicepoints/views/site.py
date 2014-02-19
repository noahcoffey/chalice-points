import os, sys

from flask import Flask, request, redirect, url_for, \
    abort, render_template, jsonify, send_from_directory, \
    Response, g, Blueprint, current_app

from flask.ext.login import login_required, current_user, logout_user

import chalicepoints
from chalicepoints import open_id, login_manager

site = Blueprint('site', __name__)

@site.route('/')
@login_required
def index():
    return render_template('index.html',
        user_json=current_user.to_json(for_public=True))

@site.route('/login')
@open_id.loginhandler
def login():
    return open_id.try_login('https://www.google.com/accounts/o8/id', \
        ask_for=['email', 'fullname'])

@site.route('/logout')
@login_required
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
