#!/usr/bin/env python
import os, sys, string
import redis
import json
import random
import urllib, urllib2
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

def getUsers():
    usersKey = 'cpUsers';

    users = {}
    if r.exists(usersKey):
        userDict = r.hgetall(usersKey)

        for userKey in userDict:
            userJSON = userDict[userKey]
            user = json.loads(userJSON);
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
    sourceKey = toKey(source)
    givenKey = 'cpEvents' + sourceKey
    given = {
        'type': 'give',
        'user': target,
        'amount': amount,
        'date': eventDate,
        'message': message,
    };
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
def index():
    return render_template('index.html')

@app.route('/api/1.0/leaderboard.json', methods=['GET'])
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
def userAction():
    userDict = getUsers()
    userNames = userDict.keys()
    userNames.sort()

    users = []
    for name in userNames:
        entry = {
            'name': name,
        }
        users.append(entry)

    return Response(json.dumps(users), mimetype='application/json')

@app.route('/api/1.0/user/<name>.json', methods=['GET'])
def userNameAction(name):
    name = name.encode('ascii')

    if name == 'list':
        return userAction()

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
def matrixAction():
    return matrix_mode('received')

@app.route('/api/1.0/matrix/<mode>.json', methods=['GET'])
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
def pointAction():
    points = getPoints()
    return jsonify(success=1, points=points)

@app.route('/api/1.0/event.json', methods=['GET', 'POST'])
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
    source = data['source'].encode('ascii')
    target = data['target'].encode('ascii')
    amount = max(min(5, data['amount']), 1)

    message = 'None'
    if 'message' in data and data['message']:
        message = data['message'].encode('ascii')

    eventDate = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    addEvent(source, target, eventDate, amount, message)

    return jsonify(success=1)

'''
@app.route('/api/1.0/event/<source>/<target>/<date>.json', methods=['DELETE'])
def removeEventAction(source, target, date):
    removeEvent(source, target, date)

    return jsonify(success=1)
'''

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
