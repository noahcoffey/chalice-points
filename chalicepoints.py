#!/usr/bin/env python
import os, sys, string
import redis
import json
import random
import urllib, urllib2
from datetime import datetime
from flask import Flask, request, redirect, url_for, \
    abort, render_template, jsonify, send_from_directory, \
    Response, g

from flask.ext.login import LoginManager, UserMixin, login_required,\
    login_user, current_user, logout_user
from flask.ext.openid import OpenID

class BadRequest(Exception):
    message = 'Bad Request'
    status_code = 400

    def __init__(self, message=None, status_code=None, payload=None):
        Exception.__init__(self)
        if message is not None:
            self.message = message

        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__, static_folder=os.path.join(PROJECT_ROOT, 'public'),
        static_url_path='/public')

app.config.from_pyfile('FlaskConfig.py')
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY', None)

if app.config['SECRET_KEY'] is None:
    abort(500)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
open_id = OpenID(app)

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r = redis.from_url(redis_url)

def updateHipchat(giver, receiver, amount, message):
    authToken = os.getenv('HIPCHAT_AUTH_TOKEN', None)
    room = os.getenv('HIPCHAT_ROOM', None)

    if not authToken or not room:
        return False

    sender = os.getenv('HIPCHAT_SENDER', 'ChalicePoints')
    color = os.getenv('HIPCHAT_COLOR', 'green')
    msgFormat = os.getenv('HIPCHAT_FORMAT', 'text')

    url = 'http://chalicepoints.formstack.com/#/user/%s' % (urllib.quote(receiver))
    points = 'Point' if amount == 1 else 'Points'
    message = '(chalicepoint) %s gave %s %d Chalice %s: %s (%s)' % (giver, receiver, amount, points, message, url)

    args = {
        'room_id': room,
        'message': message,
        'from': sender,
        'color': color,
        'message_format': msgFormat,
        'notice': 0,
    }

    data = urllib.urlencode(args)

    apiUrl = 'https://api.hipchat.com/v1/rooms/message?auth_token=%s' % (authToken)
    request = urllib2.Request(apiUrl, data)
    result = urllib2.urlopen(request)

def toKey(name):
    name = name.encode('ascii')
    key = string.translate(name, None, ' ')
    key = string.translate(key, None, '-')

    return key

def getEvents(name, deleted=None):
    userKey = toKey(name)
    eventsKey = 'cpEvents' + userKey

    events = []
    if r.exists(eventsKey):
        eventsLen = r.llen(eventsKey)
        for idx in range(eventsLen):
            eventJSON = r.lindex(eventsKey, idx)
            event = json.loads(eventJSON)

            if not deleted and '__deleted' in event:
                continue

            events.append(event)

    return events

def get_user_dict():
    users_key = 'cpUsers'

    user_dict = None
    if r.exists(users_key):
        user_dict = r.hgetall(users_key)

    return user_dict

def get_user_names():
    names = []

    user_dict = get_user_dict()
    if user_dict != None:
        for user_key in user_dict:
            user_json = user_dict[user_key]
            user = json.loads(user_json)
            names.append(user['name'])

    return names

def get_user_emails():
    emails = {}
    user_dict = get_user_dict()
    if user_dict != None:
        for user_key in user_dict:
            user_json = user_dict[user_key]
            user = json.loads(user_json)
            emails[user['email']] = user['name']

    return emails

def getUsers():
    users = {}

    user_dict = get_user_dict()
    if user_dict != None:
        for user_key in user_dict:
            user_json = user_dict[user_key]
            user = json.loads(user_json)
            users[user['name']] = user

    return users

def getPoints():
    points = {}

    users = getUsers()
    for source in users:
        if source not in points:
            points[source] = {
                'givenTotal': 0,
                'receivedTotal': 0,
                'given': {},
                'received': {},
            }

        events = getEvents(source)
        for event in events:
            target = event['user']
            amount = int(event['amount'])

            if event['type'] == 'give':
                points[source]['givenTotal'] += amount

                if target not in points[source]['given']:
                    points[source]['given'][target] = 0

                points[source]['given'][target] += amount
            else:
                points[source]['receivedTotal'] += amount

                if target not in points[source]['received']:
                    points[source]['received'][target] = 0

                points[source]['received'][target] += amount

    return points

def addEvent(source, target, eventDate, amount, message):
    if source == target:
        return False

    sourceKey = toKey(source)
    givenKey = 'cpEvents' + sourceKey
    given = {
        'type': 'give',
        'user': target,
        'amount': amount,
        'date': eventDate,
        'message': message,
    }
    r.lpush(givenKey, json.dumps(given))

    targetKey = toKey(target)
    receivedKey = 'cpEvents' + targetKey
    received = {
        'type': 'receive',
        'user': source,
        'amount': amount,
        'date': eventDate,
        'message': message,
    }
    r.lpush(receivedKey, json.dumps(received))

    updateHipchat(source, target, amount, message)

'''
def removeEvent(source, target, date):
    source = source.encode('ascii')
    target = target.encode('ascii')
    date = date.encode('ascii')

    found = False

    sourceEvents = getEvents(source)
    for idx in range(len(sourceEvents)):
        event = sourceEvents[idx]
        if event['user'] == target and event['date'] == date:
            found = True
            setDeletedFlag(source, idx, event, True)

    targetEvents = getEvents(target)
    for idx in range(len(targetEvents)):
        event = targetEvents[idx]
        if event['user'] == source and event['date'] == date:
            found = True
            setDeletedFlag(source, idx, event, True)

    return found

def setDeletedFlag(key, idx, event, deleted=True):
    if deleted:
        event['__deleted'] = 1
    else:
        event.pop('__deleted', None)

    r.lset(key, idx, json.dumps(event))
'''


@app.route('/')
@login_required
def index():
    return render_template('index.html',
        user_json=current_user.to_json(for_public=True))

@app.route('/api/1.0/totals.json', methods=['GET'])
@login_required
def totalsActions():
    totals = {}
    leaders = {}
    highest = {}

    users = getUsers()
    for source in users:
        events = getEvents(source)
        for event in events:
            target = event['user']
            amount = int(event['amount'])

            week = datetime.strptime(event['date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%U %y 0')
            date = datetime.strptime(week, '%U %y %w').strftime('%Y-%m-%dT%H:%M:%SZ')

            if not date in totals:
                totals[date] = {}

            if not source in totals[date]:
                totals[date][source] = {
                    'given': 0,
                    'received': 0,
                }

            if not target in totals[date]:
                totals[date][target] = {
                    'given': 0,
                    'received': 0,
                }

            if event['type'] == 'give':
                totals[date][source]['given'] += amount
                totals[date][target]['received'] += amount

    for date in totals:
        leaders[date] = {
            'date': date,
            'given': [],
            'received': [],
        }

        highest[date] = {
            'given': 0,
            'received': 0,
        }

        for person in totals[date]:
            if totals[date][person]['given'] > highest[date]['given']:
                leaders[date]['given'] = [{
                    'name': person,
                    'amount': totals[date][person]['given'],
                }]

                highest[date]['given'] = totals[date][person]['given']
            elif totals[date][person]['given'] == highest[date]['given']:
                leaders[date]['given'].append({
                    'name': person,
                    'amount': totals[date][person]['given'],
                })

            if totals[date][person]['received'] > highest[date]['received']:
                leaders[date]['received'] = [{
                    'name': person,
                    'amount': totals[date][person]['received'],
                }]

                highest[date]['received'] = totals[date][person]['received']
            elif totals[date][person]['received'] == highest[date]['received']:
                leaders[date]['received'].append({
                    'name': person,
                    'amount': totals[date][person]['received'],
                })

    return Response(json.dumps(leaders.values()), mimetype='application/json')

@app.route('/api/1.0/leaderboard.json', methods=['GET'])
@login_required
def leaderboardAction():
    points = getPoints()

    given = []
    received = []
    for name in points:
        givenEntry = {
            'name': name,
            'amount': points[name]['givenTotal']
        }
        given.append(givenEntry)

        receivedEntry = {
            'name': name,
            'amount': points[name]['receivedTotal']
        }
        received.append(receivedEntry)

    return jsonify(success=1, given=given, received=received)

@app.route('/api/1.0/user.json', methods=['GET'])
@login_required
def userAction(include_self=True):
    userDict = getUsers()
    userNames = userDict.keys()
    userNames.sort()

    users = []
    for name in userNames:
        if name == current_user.name and not include_self:
            continue

        entry = {
            'name': name,
        }
        users.append(entry)

    return Response(json.dumps(users), mimetype='application/json')

@app.route('/api/1.0/user/<name>.json', methods=['GET'])
@login_required
def userNameAction(name):
    name = name.encode('ascii')

    if name == 'list':
        return userAction(False)

    users = getUsers()
    if name not in users:
        abort(404)

    user = users[name]
    user['events'] = getEvents(name)
    user['given'] = 0
    user['received'] = 0

    points = getPoints()
    if name in points:
        user['given'] = points[name]['givenTotal']
        user['received'] = points[name]['receivedTotal']

    return Response(json.dumps(user), mimetype='application/json')

@app.route('/api/1.0/matrix.json', methods=['GET'])
@login_required
def matrixAction():
    return matrix_mode('received')

@app.route('/api/1.0/matrix/<mode>.json', methods=['GET'])
@login_required
def matrixModeAction(mode):
    points = getPoints()
    users = getUsers()

    names = users.keys()
    names.sort()

    if mode == 'received':
        matrix = []
        for user in names:
            entry = []

            for otherUser in names:
                value = 0
                if user in points and otherUser in points[user]['received']:
                    value = points[user]['received'][otherUser]

                entry.append(value)

            matrix.append(entry)
    else:
        matrix = []
        for user in names:
            entry = []

            for otherUser in names:
                value = 0
                if user in points and otherUser in points[user]['given']:
                    value = points[user]['given'][otherUser]

                entry.append(value)

            matrix.append(entry)

    return Response(json.dumps(matrix), mimetype='application/json')

@app.route('/api/1.0/point.json', methods=['GET'])
@login_required
def pointAction():
    points = getPoints()
    return jsonify(success=1, points=points)

@app.route('/api/1.0/event.json', methods=['GET', 'POST'])
@login_required
def eventAction():
    if request.method == 'GET':
        return eventGetAction()
    elif request.method == 'POST':
        return eventPostAction(request.json)
    else:
        abort(404)

def eventGetAction():
    events = {}

    users = getUsers()
    for name in users:
        events[name] = getEvents(name)

    return jsonify(success=1, events=events)

def eventPostAction(data):
    source = current_user.name
    target = data['target'].encode('ascii')
    amount = max(min(5, data['amount']), 1)

    if target == current_user.name:
        abort(403)

    users = get_user_names()
    if target not in users:
        abort(403)

    message = 'None'
    if 'message' in data and data['message']:
        message = data['message'].encode('ascii')

    eventDate = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    addEvent(source, target, eventDate, amount, message)

    return jsonify(success=1)

'''
@app.route('/api/1.0/event/<source>/<target>/<date>.json', methods=['DELETE'])
@login_required
def removeEventAction(source, target, date):
    removeEvent(source, target, date)

    return jsonify(success=1)
'''

@app.route('/login')
@open_id.loginhandler
def login():
    return open_id.try_login('https://www.google.com/accounts/o8/id', \
        ask_for=['email'])

@app.route('/logout')
@login_required
def logout():
    r.hdel('openid', current_user.url)
    logout_user()
    return redirect(url_for('index'))

@open_id.after_login
def after_login(response):
    email = string.lower(response.email)

    emails = get_user_emails()
    if email not in emails:
        abort(401)

    user = User(response.identity_url, email, emails[email])
    user_json = user.to_json()
    r.hset('openid', user.url, user_json)
    login_user(user)

    return redirect(url_for('index'))

class User(UserMixin):
    def __init__(self, url, email, name):
        self.url = url
        self.email = email
        self.name = name

    def get_id(self):
        return self.url

    def to_json(self, for_public=False):
        d = { 'email' : self.email, 'name' : self.name }
        if not for_public:
            d['url'] = self.url

        return json.dumps(d)

@login_manager.user_loader
def load_user(id):
    user_json = r.hget('openid', id)
    if user_json:
        u = json.loads(user_json)
        return User(u['url'], u['email'], u['name'])
    else:
        return None

@app.route('/humans.txt')
def humans():
    return send_from_directory(os.path.join(app.root_path, 'public'),
        'humans.txt', mimetype='text/plain')

@app.route('/robots.txt')
def robots():
    return send_from_directory(os.path.join(app.root_path, 'public'),
        'robots.txt', mimetype='text/plain')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'public'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.route('/googleaf18a4916e849528.html')
def gwt():
    return send_from_directory(os.path.join(app.root_path, 'public'),
        'googleaf18a4916e849528.html', mimetype='text/html')

@app.errorhandler(BadRequest)
def handle_bad_request(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

if __name__ == "__main__":
    port = 9896
    if len(sys.argv) == 2:
        port = int(sys.argv[1])

    app.run(host='0.0.0.0', port=port, debug=True)
