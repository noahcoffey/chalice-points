import os, sys, string
import json
import redis

from flask import Flask, redirect, url_for, abort, jsonify
from flask.ext.login import LoginManager, login_user
from flask.ext.openid import OpenID

from chalicepoints.models.user import User

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__, static_folder=os.path.join(PROJECT_ROOT, 'public'),
        static_url_path='/public')

app.config.from_object('chalicepoints.config.DefaultConfig')
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY', app.config['SECRET_KEY'])

if app.config['SECRET_KEY'] is None:
    abort(500)

# Flask-OpenID
open_id = OpenID()
open_id.init_app(app)

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'site.login'
login_manager.init_app(app)

# Redis
redis_url = os.getenv('REDISTOGO_URL', app.config['REDIS_URL'])
r = redis.from_url(redis_url)

def register_blueprint(app):
    from chalicepoints.views.site import site
    app.register_blueprint(site)

    from chalicepoints.views.api import api
    app.register_blueprint(api)

register_blueprint(app)

@login_manager.user_loader
def load_user(id):
    from chalicepoints.models.user import User

    user_json = r.hget('openid', id)
    if user_json:
        u = json.loads(user_json)
        return User.get_instance(u['email'])
    else:
        return None

@open_id.after_login
def after_login(response):
    from chalicepoints.models.user import User

    email = string.lower(response.email)

    user = User.get_instance(email)
    if not user:
        abort(401)

    user.set_id(response.identity_url)

    user_json = user.to_json()
    r.hset('openid', , user_json)
    login_user(user)

    return redirect(url_for('site.index'))

if __name__ == "__main__":
    port = 9896
    if len(sys.argv) == 2:
        port = int(sys.argv[1])

    app.run(host='0.0.0.0', port=port, debug=True)
