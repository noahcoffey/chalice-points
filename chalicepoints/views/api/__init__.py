import os, sys
import json
from datetime import datetime, timedelta
import urllib, urllib2

from flask import Blueprint, abort, request, jsonify, Response
from flask.ext.login import login_required, current_user

from chalicepoints.models.user import User, UserModelJSONEncoder as Encoder
from chalicepoints.models.event import Event

from peewee import *

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/1.0/timeline', methods=['GET'])
@login_required
def timeline():
    timeline = Event.get_timeline()
    return Response(json.dumps(timeline, cls=Encoder), mimetype='application/json')

@api.route('/1.0/winners', methods=['GET'])
@login_required
def winners():
    totals = {}
    leaders = {}
    highest = {}

    current_week = datetime.now().strftime('%U %y 0')
    current_date = datetime.strptime(current_week, '%U %y %w').strftime('%Y-%m-%dT%H:%M:%S')

    q = Event.select()
    for event in q:
        week = event.created_at.strftime('%U %y 0')
        date = datetime.strptime(week, '%U %y %w').strftime('%Y-%m-%dT%H:%M:%S')

        if not date in totals:
            totals[date] = {}

        if not event.source.id in totals[date]:
            totals[date][event.source.id] = event.source
            totals[date][event.source.id].given = 0
            totals[date][event.source.id].received = 0

        if not event.target.id in totals[date]:
            totals[date][event.target.id] = event.target
            totals[date][event.target.id].given = 0
            totals[date][event.target.id].received = 0

        totals[date][event.source.id].given += event.amount
        totals[date][event.target.id].received += event.amount

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
            if totals[date][person].given > highest[date]['given']:
                leaders[date]['given'] = [{
                    'user': totals[date][person],
                    'amount': totals[date][person].given
                }]

                highest[date]['given'] = totals[date][person].given
            elif totals[date][person].given == highest[date]['given']:
                leaders[date]['given'].append({
                    'user': totals[date][person],
                    'amount': totals[date][person].given
                })

            if totals[date][person].received > highest[date]['received']:
                leaders[date]['received'] = [{
                    'user': totals[date][person],
                    'amount': totals[date][person].received
                }]

                highest[date]['received'] = totals[date][person].received
            elif totals[date][person].received == highest[date]['received']:
                leaders[date]['received'].append({
                    'user': totals[date][person],
                    'amount': totals[date][person].received
                })

    return Response(json.dumps(leaders.values(), cls=Encoder), mimetype='application/json')

@api.route('/1.0/leaderboard/<type>', methods=['GET'])
@login_required
def leaderboard(type):
    points = Event.get_points(type == 'week')

    given = []
    received = []

    for id, user in points.iteritems():
        givenEntry = {
            'user': user,
            'amount': user.given
        }
        given.append(givenEntry)

        receivedEntry = {
            'user': user,
            'amount': user.received
        }
        received.append(receivedEntry)

    response = {
        'success': 1,
        'given': given,
        'received': received
    }

    return Response(json.dumps(response, cls=Encoder), mimetype='application/json')

@api.route('/1.0/merge/<id>/<target>', methods=['POST'])
@login_required
def mergeUser(id, target):
    Event.update(source=target).where(Event.source == id).execute()
    Event.update(target=target).where(Event.target == id).execute()

    try:
        user = User.get(User.id == id)
        user.delete_instance()
    except DoesNotExist:
        abort(404)

    return jsonify(success=1)

@api.route('/1.0/user', methods=['GET'])
@login_required
def userAction(include_self=True, include_points=False, include_events=False):
    users = User.get_users(include_self, include_points, include_events)
    return Response(json.dumps(users, cls=Encoder), mimetype='application/json')

@api.route('/1.0/user/<id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def userNameAction(id):
    if request.method == 'GET':
        id = id.encode('ascii')

        if id == 'list':
            return userAction(False)

        if id == 'all':
            return userAction(True, True)

        user = User.get(User.id == id)
        user.events = user.get_timeline()
        user.points = user.get_points()

        return Response(json.dumps(user, cls=Encoder), mimetype='application/json')
    elif request.method == 'PUT':
        if not current_user.elder:
            abort(403)

        data = request.json
        user = User(**data)
        user.save()
        return jsonify(success=1)
    elif request.method == 'DELETE':
        if not current_user.elder:
            abort(403)

        try:
            user = User.get(User.id == id)
            user.delete_instance()
        except DoesNotExist:
            abort(404)

        return jsonify(success=1)

@api.route('/1.0/matrix', methods=['GET'])
@login_required
def matrixAction():
    return matrixModeAction('received')

@api.route('/1.0/matrix/<mode>', methods=['GET'])
@login_required
def matrixModeAction(mode):
    users = User.get_users()
    matrix = {}

    q = Event.select()
    for event in q:
        user_one = event.source.id
        user_two = event.target.id

        if mode == 'received':
            user_one = event.target.id
            user_two = event.source.id

        if user_one not in matrix:
            matrix[user_one] = {}

        if user_two not in matrix[user_one]:
            matrix[user_one][user_two] = 0

        matrix[user_one][user_two] += event.amount

    entries = []
    for user in users:
        entry = []
        for other_user in users:
            value = 0
            if user.id in matrix and other_user.id in matrix[user.id]:
                value = matrix[user.id][other_user.id]
            entry.append(value)
        entries.append(entry)

    return Response(json.dumps(entries, cls=Encoder), mimetype='application/json')

@api.route('/1.0/event', methods=['GET', 'POST'])
@login_required
def eventAction():
    if request.method == 'GET':
        users = User.get_users()
        events = dict((user.name, user.get_timeline()) for user in users)

        response = {
            'success': 1,
            'events': events
        }

        return Response(json.dumps(response, cls=Encoder), mimetype='application/json')
    elif request.method == 'POST':
        data = request.json
        data.pop('id', None)

        if data['target'] == current_user.id:
            abort(403)

        target = User()
        try:
            target = User.get(User.id == data['target'])
        except DoesNotExist:
            abort(403)

        if target.disabled:
            abort(403)

        data['amount'] = max(min(current_user.max_points, int(data['amount'])), 1)

        event = Event(**data)
        event.source = current_user.id
        event.add()

        return jsonify(success=1)

    abort(404)

@api.route('/1.0/event/<id>', methods=['PUT', 'DELETE'])
@login_required
def eventIdAction(id):
    if request.method == 'DELETE':
        try:
            event = Event.get(Event.id == id)
            event.delete_instance()
        except DoesNotExist:
            abort(404)

        return jsonify(success=1)
    elif request.method == 'PUT':
        data = request.json
        data.pop('target_user', None)
        data.pop('source_user', None)
        data.pop('type', None)

        if data['source'] != current_user.id and current_user.elder == 0:
            abort(403)

        target = None
        try:
            target = User.get(User.id == data['target'])
        except DoesNotExist:
            abort(403)

        if target.disabled and current_user.elder == 0:
            abort(403)

        data['amount'] = max(min(current_user.max_points, data['amount']), 1)

        event = Event(**data)
        event.save()

        return jsonify(success=1)

    abort(404)
