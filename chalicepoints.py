import os, sys, string
import redis
import json
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

@app.route('/api/1.0/users.json', methods=['GET'])
def users():
    users = []
    userList = userlist()
    for name in userList:
        entry = {
            'name': name,
        }

        users.append(entry)

    return Response(json.dumps(users), mimetype='application/json')

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

    key = 'cpPoints' + string.translate(source, None, ' ')
    field = string.replace(target, ' ', '_')
    r.hincrby(key, field, amount)

    return jsonify(success=1)

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
    app.run(host='0.0.0.0', port=9898, debug=True)
