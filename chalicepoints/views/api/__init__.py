import os, sys
import simplejson as json
from datetime import datetime, timedelta, time
import urllib, urllib2

from flask import Blueprint, abort, request, jsonify, Response, current_app
from flask.ext.login import login_required, current_user

from chalicepoints.models.user import User, UserModelJSONEncoder as Encoder
from chalicepoints.models.event import Event

from peewee import *
from playhouse.shortcuts import *

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/1.0/history/all', methods=['POST'])
@login_required
def history_all():
  query = request.json

  Source = User.alias()
  Target = User.alias()

  history = Event.select(
    Event.id, Event.source, Event.target, Event.type, Event.amount, Event.created_at, Source.name.alias('source_name'), Target.name.alias('target_name')
  ).join(
    Source, on=(Event.source == Source.id)
  ).switch(Event).join(
    Target, on=(Event.target == Target.id)
  ).switch(Event)

  # Process Query Parameters
  history = process_history_query(history, query)

  # Order By
  order_by = Event.created_at.desc()

  if 'sort' in query and query['sort'] is not None:
    field = query['sort']['field'] if 'field' in query['sort'] else 'created_at'

    if field == 'source':
      field = 'source_name'
    elif field == 'target':
      field = 'target_name'

    order_by = SQL('%s %s' % (field, query['sort']['direction']))

  history = history.order_by(order_by)

  # Get Result Count
  count = history.count()

  # Paginate
  page = 1
  limit = 10

  if 'page' in query and query['page'] is not None:
    page = query['page']

  if 'limit' in query and query['limit'] is not None:
    limit = query['limit']

  history = history.paginate(page, limit)

  # Query and return as dictionary
  history = history.dicts()

  # Process results
  events = []
  for event in history:
    event['type'] = event['type'] if event['type'] != '' else 'other'
    events.append(event)

  result = {
    'history': events,
    'count': count
  }

  return Response(json.dumps(result, cls=Encoder, use_decimal=True), mimetype='application/json')

@api.route('/1.0/history/source', methods=['POST'])
@login_required
def history_by_source():
  query = request.json

  Source = User.alias()
  Target = User.alias()

  history = Event.select(
    Event.id, Event.source, Source.name.alias('source_name'), fn.Sum(Event.amount).alias('amount')
  ).join(
    Source, on=(Event.source == Source.id)
  ).switch(Event)

  # Group by Giver
  history = history.group_by(Event.source)

  # Process Query Parameters
  history = process_history_query(history, query)

  # Order By
  history = history.order_by(SQL('amount DESC'))

  # Get Result Count
  count = history.count()

  # Paginate
  page = 1
  limit = 5

  if 'page' in query and query['page'] is not None:
    page = query['page']

  if 'limit' in query and query['limit'] is not None:
    limit = query['limit']

  history = history.paginate(page, limit)

  # Query and return as dictionary
  history = history.dicts()

  # Process results
  events = []
  for event in history:
    events.append(event)

  result = {
    'history': events,
    'count': count
  }

  return Response(json.dumps(result, cls=Encoder, use_decimal=True), mimetype='application/json')

@api.route('/1.0/history/target', methods=['POST'])
@login_required
def history_by_target():
  query = request.json

  Source = User.alias()
  Target = User.alias()

  history = Event.select(
    Event.id, Event.target, Target.name.alias('target_name'), fn.Sum(Event.amount).alias('amount')
  ).join(
    Target, on=(Event.target == Target.id)
  ).switch(Event)

  # Group by Target
  history = history.group_by(Event.target)

  # Process Query Parameters
  history = process_history_query(history, query)

  # Order By
  history = history.order_by(SQL('amount DESC'))

  # Get Result Count
  count = history.count()

  # Paginate
  page = 1
  limit = 5

  if 'page' in query and query['page'] is not None:
    page = query['page']

  if 'limit' in query and query['limit'] is not None:
    limit = query['limit']

  history = history.paginate(page, limit)

  # Query and return as dictionary
  history = history.dicts()

  # Process results
  events = []
  for event in history:
    events.append(event)

  result = {
    'history': events,
    'count': count
  }

  return Response(json.dumps(result, cls=Encoder, use_decimal=True), mimetype='application/json')

@api.route('/1.0/history/type', methods=['POST'])
@login_required
def history_by_type():
  query = request.json

  history = Event.select(
    Event.id, Event.type, fn.Sum(Event.amount).alias('amount')
  )

  # Group by Type
  history = history.group_by(Event.type)

  # Process Query Parameters
  history = process_history_query(history, query)

  # Order By
  history = history.order_by(SQL('amount DESC'))

  # Get Result Count
  count = history.count()

  # Paginate
  page = 1
  limit = 5

  if 'page' in query and query['page'] is not None:
    page = query['page']

  if 'limit' in query and query['limit'] is not None:
    limit = query['limit']

  history = history.paginate(page, limit)

  # Query and return as dictionary
  history = history.dicts()

  # Process results
  events = []
  for event in history:
    event['type'] = event['type'] if event['type'] != '' else 'other'
    events.append(event)

  result = {
    'history': events,
    'count': count
  }

  return Response(json.dumps(result, cls=Encoder, use_decimal=True), mimetype='application/json')

@api.route('/1.0/leaderboard/<type>', methods=['GET'])
@login_required
def leaderboard(type):
  points = Event.get_points(type)

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
def userAction():
  users = User.get_users()

  return Response(json.dumps(users, cls=Encoder), mimetype='application/json')

@api.route('/1.0/user/targets', methods=['GET'])
@login_required
def userTargetsAction():
  users = User.get_users(include_self=False, exclude_disabled=True)
  return Response(json.dumps(users, cls=Encoder), mimetype='application/json')

@api.route('/1.0/user/<id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def userNameAction(id):
  if request.method == 'GET':
    try:
      user = User.get_user(id, include_points=True)
    except DoesNotExist:
      abort(404)

    return Response(json.dumps(user, cls=Encoder), mimetype='application/json')
  elif request.method == 'PUT':
    if not current_user.elder:
      abort(403)

    data = request.json
    data['settings'] = json.dumps(data['settings']) if 'settings' in data else '{}'

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

@api.route('/1.0/user/<id>/timeline', methods=['GET', 'PUT', 'DELETE'])
@login_required
def userTimelineAction(id):
  try:
    user = User.get(User.id == id)
  except DoesNotExist:
    abort(404)

  events = user.get_timeline()

  return Response(json.dumps(events, cls=Encoder), mimetype='application/json')

@api.route('/1.0/event', methods=['POST'])
@login_required
def eventAction():
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
    data['source'] = data['source']['id']
    data['target'] = data['target']['id']
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

def process_history_query(history, query):
  if 'minDate' in query and query['minDate'] is not None:
    history = history.where(fn.Date(Event.created_at) >= query['minDate'])

  if 'maxDate' in query and query['maxDate'] is not None:
    history = history.where(fn.Date(Event.created_at) <= query['maxDate'])

  if 'filters' in query:
    if 'other' in query['filters'] and query['filters']['other'] == '1':
      history = history.where((Event.type != 'other') & (Event.type != ''))

  return history
