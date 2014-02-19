import os, sys
import json
from datetime import datetime
import urllib, urllib2

from flask import Blueprint, abort, request, jsonify, Response
from flask.ext.login import login_required, current_user

from chalicepoints.models.user import User
from chalicepoints.models.event import Event
from chalicepoints.models.point import Point

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/1.0/timeline.json', methods=['GET'])
@login_required
def timeline():
    timeline = Event.get_timeline()
    return Response(json.dumps(timeline.values()), mimetype='application/json')

@api.route('/1.0/winners.json', methods=['GET'])
@login_required
def winners():
    totals = {}
    leaders = {}
    highest = {}

    current_week = datetime.now().strftime('%U %y 0')
    current_date = datetime.strptime(current_week, '%U %y %w').strftime('%Y-%m-%dT%H:%M:%S')

    users = User.get_users()
    for source in users:
        events = Event.get_events(source)
        for event in events:
            target = event['user']
            amount = int(event['amount'])

            week = datetime.strptime(event['date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%U %y 0')
            date = datetime.strptime(week, '%U %y %w').strftime('%Y-%m-%dT%H:%M:%S')

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
            'current': 0,
            'given': [],
            'received': [],
        }

        if current_date == date:
            leaders[date]['current'] = 1

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

@api.route('/1.0/leaderboard/<type>.json', methods=['GET'])
@login_required
def leaderboard(type):
    week = False
    if type == 'week':
        week = True

    points = Point.get_points(week)

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

@api.route('/1.0/user.json', methods=['GET'])
@login_required
def userAction(include_self=True):
    user_dict = User.get_users()
    user_names = user_dict.keys()
    user_names.sort()

    users = []
    for name in user_names:
        if name == current_user.name and not include_self:
            continue

        entry = user_dict[name]
        users.append(entry)

    return Response(json.dumps(users), mimetype='application/json')

@api.route('/1.0/user/<name>.json', methods=['GET'])
@login_required
def userNameAction(name):
    name = name.encode('ascii')

    if name == 'list':
        return userAction(False)

    users = User.get_users()
    if name not in users:
        abort(404)

    user = users[name]
    user['events'] = Event.get_events(name)
    user['given'] = 0
    user['received'] = 0

    points = Point.get_points()
    if name in points:
        user['given'] = points[name]['givenTotal']
        user['received'] = points[name]['receivedTotal']

    return Response(json.dumps(user), mimetype='application/json')

@api.route('/1.0/matrix.json', methods=['GET'])
@login_required
def matrixAction():
    return matrix_mode('received')

@api.route('/1.0/matrix/<mode>.json', methods=['GET'])
@login_required
def matrixModeAction(mode):
    points = Point.get_points()
    users = User.get_users()

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

@api.route('/1.0/point.json', methods=['GET'])
@login_required
def pointAction():
    points = Point.get_points()
    return jsonify(success=1, points=points)

@api.route('/1.0/event.json', methods=['GET', 'POST'])
@login_required
def eventAction():
    if request.method == 'GET':
        return Event.do_get_events()
    elif request.method == 'POST':
        return Event.do_post_events(request.json)
    else:
        abort(404)

@api.route('/1.0/event/<source>/<target>/<date>.json', methods=['DELETE'])
@login_required
def removeEventAction(source, target, date):
    Event.remove_event(source, target, date)
    return jsonify(success=1)
