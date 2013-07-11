#!/usr/bin/env python
import os, sys, string
import redis
import json
import random
from datetime import datetime
from flask import Flask, request, redirect, url_for, \
    abort, render_template, jsonify, send_from_directory, \
    Response

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

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r = redis.from_url(redis_url)

def points_given(username):
    key = 'cpPoints' + string.translate(username, None, ' ')
    if r.exists(key):
        return r.hgetall(key)

    return None

def userlist():
    users = []
    usersLen = r.llen('cpUsers')
    for idx in range(usersLen):
        user = r.lindex('cpUsers', idx)
        users.append(user)

    users.sort()

    return users

def points():
    given = {}
    received = {}

    givenTotals = {}
    receivedTotals = {}

    users = userlist()
    for username in users:
        points = points_given(username)
        if points == None:
            continue

        for key in points.keys():
            name = string.replace(key, '_', ' ')

            pointValue = int(points[key])

            if username not in given:
                given[username] = {}

            given[username][name] = pointValue

            if username not in givenTotals:
                givenTotals[username] = 0

            givenTotals[username] += pointValue

            if name not in received:
                received[name] = {}

            received[name][username] = pointValue

            if name not in receivedTotals:
                receivedTotals[name] = 0

            receivedTotals[name] += pointValue

    return [given, received, givenTotals, receivedTotals]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/1.0/leaderboard.json', methods=['GET'])
def leaderboard():
    givenDict, receivedDict, givenTotals, receivedTotals = points()

    given = []
    for name in givenTotals.keys():
        entry = {
            'name': name,
            'amount': givenTotals[name],
        }

        given.append(entry)

    received = []
    for name in receivedTotals.keys():
        entry = {
            'name': name,
            'amount': receivedTotals[name],
        }

        received.append(entry)

    return jsonify(success=1, given=given, received=received)

@app.route('/api/1.0/user.json', methods=['GET'])
def users():
    skip = ['Duane Hunt'];

    users = []
    userList = userlist()
    for name in userList:
        if name in skip:
            continue

        entry = {
            'name': name,
        }

        users.append(entry)

    return Response(json.dumps(users), mimetype='application/json')

@app.route('/api/1.0/user/<name>.json', methods=['GET'])
def user(name):
    if name == 'list':
        return users()

    key = string.translate(name.encode('ascii'), None, ' ')
    key = string.translate(key, None, '-')

    userKey = 'cpUser' + key
    if not r.exists(userKey):
        abort(404)

    user = r.hgetall(userKey)
    user['events'] = []

    eventKey = 'cpEvents' + key
    if r.exists(eventKey):
        eventsLen = r.llen(eventKey)
        for idx in range(eventsLen):
            event = r.lindex(eventKey, idx)
            if '__deleted' in event:
                continue

            user['events'].append(json.loads(event))

    givenDict, receivedDict, givenTotals, receivedTotals = points()

    user['given'] = 0
    if user['name'] in givenTotals:
        user['given'] = givenTotals[user['name']]

    user['received'] = 0
    if user['name'] in receivedTotals:
        user['received'] = receivedTotals[user['name']]

    return Response(json.dumps(user), mimetype='application/json')

@app.route('/api/1.0/matrix.json', methods=['GET'])
def matrix():
    return matrix_mode('received')

@app.route('/api/1.0/matrix/<mode>.json', methods=['GET'])
def matrix_mode(mode):
    givenDict, receivedDict, givenTotals, receivedTotals = points()
    users = userlist()

    if mode == 'received':
        matrix = []
        for user in users:
            entry = []

            for otherUser in users:
                value = 0
                if user in receivedDict and otherUser in receivedDict[user]:
                    value = receivedDict[user][otherUser]

                entry.append(value)

            matrix.append(entry)
    else:
        matrix = []
        for user in users:
            entry = []

            for otherUser in users:
                value = 0
                if user in givenDict and otherUser in givenDict[user]:
                    value = givenDict[user][otherUser]

                entry.append(value)

            matrix.append(entry)

    return Response(json.dumps(matrix), mimetype='application/json')

@app.route('/api/1.0/point.json', methods=['POST'])
def savePoint():
    source = request.json['source'].encode('ascii')
    target = request.json['target'].encode('ascii')
    amount = request.json['amount']

    if amount < 1:
        amount = 1
    elif amount > 5:
        amount = 5

    message = 'None'
    if 'message' in request.json and request.json['message']:
        message = request.json['message'].encode('ascii')

    sourceKey = string.translate(source, None, ' ')
    targetKey = string.translate(target, None, ' ')

    pointsKey = 'cpPoints' + sourceKey
    field = string.replace(target, ' ', '_')
    r.hincrby(pointsKey, field, amount)

    eventDate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    givenKey = 'cpEvents' + sourceKey
    given = {
        'type': 'given',
        'user': target,
        'amount': amount,
        'reason': message,
        'date': eventDate,
    };
    r.lpush(givenKey, json.dumps(given))

    receivedKey = 'cpEvents' + targetKey
    received = {
        'type': 'received',
        'user': source,
        'amount': amount,
        'reason': message,
        'date': eventDate,
    }
    r.lpush(receivedKey, json.dumps(received))

    return jsonify(success=1)

@app.route('/api/1.0/event.json', methods=['GET'])
def events():
    events = {}

    users = userlist()
    for user in users:
        key = string.translate(user, None, ' ')

        eventsKey = 'cpEvents' + key;
        if r.exists(eventskey):
            events['user'] = []

            eventsLen = r.llen(eventsKey)
            for idx in range(eventsLen):
                eventJSON = r.lindex(key, idx)
                event = json.loads(eventJSON)

                events['user'].append(event)

    return jsonify(success=1, events=events)

@app.route('/api/1.0/event/<source>/<target>/<date>.json', methods=['DELETE'])
def deleteEvent(source, target, date):
    source = source.encode('ascii')
    target = target.encode('ascii')
    date = date.encode('ascii')

    givenKey = 'cpEvents' + sourceKey
    eventsLen = r.llen(givenKey)
    for idx in range(eventsLen):
        eventJSON = r.lindex(givenKey, idx)
        event = json.loads(eventJSON)

        if event.source == source and \
           event.target == target and \
           event.date == date:

           event['__deleted'] = 1
           r.lset(givenKey, idx, json.dumps(event))

    receivedKey = 'cpEvents' + targetKey
    eventsLen = r.llen(receivedKey)
    for idx in range(eventsLen):
        eventJSON = r.lindex(givenKey, idx)
        event = json.loads(eventJSON)

        if event.source == source and \
           event.target == target and \
           event.date == date:

           event['__deleted'] = 1

           r.lset(receivedKey, idx, json.dumps(event))

    return jsonify(success=1)

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
