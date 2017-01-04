import os
import urllib
import urllib2
import chalicepoints
import simplejson as json

from datetime import datetime, timedelta
from calendar import monthrange

from flask import current_app

from peewee import *

from chalicepoints.models.base import BaseModel, BaseModelJSONEncoder as Encoder
from chalicepoints.models.user import User

class Event(BaseModel):
  source = ForeignKeyField(User, db_column='source', related_name='given')
  target = ForeignKeyField(User, db_column='target', related_name='received')
  amount = IntegerField()
  type = CharField()
  message = CharField()

  types = {
    'peer': 'Approach everyone as a peer, regardless of title',
    'agile': 'Be agile and iterate',
    'communication': 'Communicate Status',
    'transparency': 'Default to transparency with each other',
    'problemsolving': 'Get to work on solving problems',
    'helpothers': 'Help others succeed',
    'positivity': 'Inject positivity into all of your interactions',
    'results': 'Results matter',
    'growth': 'Seek growth',
    'other': 'High Five',
  }

  def add(self):
    self.save()
    self.hipchat()
    self.slack()

  def slack(self):
    if 'SLACK_AUTH_TOKEN' not in current_app.config:
      return False

    if 'SLACK_ROOM' not in current_app.config:
      return False

    authToken = current_app.config['SLACK_AUTH_TOKEN']
    room = current_app.config['SLACK_ROOM']
    siteUrl = current_app.config['SITE_URL']

    if not authToken or not room or not siteUrl:
      return False

    sender = 'ChalicePoints'
    if 'SLACK_SENDER' in current_app.config:
      sender = current_app.config['SLACK_SENDER']

    color = '#36a64f'
    if 'SLACK_COLOR' in current_app.config:
      color = current_app.config['SLACK_COLOR']

    url = '%s/user/%s' % (siteUrl, self.target.id)
    points = 'Point' if self.amount == 1 else 'Points'
    message = ':chalicepoint: %s gave %s %d Chalice %s: %s - %s (%s)' % (self.source.name, self.target.name, self.amount, points, self.types[self.type], self.message, url)

    args = {
      'token': authToken,
      'channel': room,
      'attachments': {
        'fallback': message,
        'color': color,
        'author_name': self.source.name,
        'author_link': '%s/user/%s' % (siteUrl, self.source.id),
        'author_icon': 'http://gravatar.com/avatar/%s?s=48&d=mm' % (self.source.gravatar),
        'title': 'Gave %s %d Chalice %s' % (self.target.name, self.amount, points),
        'title_link': url,
        'text': self.message,
        'fields': {
          'title': self.types[self.type],
          'short': False,
        },
        'footer': 'Chalice Points',
        'footer_icon': 'http://chalicepoints.formstack.com/public/images/chalice-48x48.png',
      },
      'username': sender,
      'as_user': False,
      'icon_url': 'http://chalicepoints.formstack.com/public/images/chalice-48x48.png',
    }

    data = urllib.urlencode(args)

    apiUrl = 'https://slack.com/api/chat.postMessage'
    request = urllib2.Request(apiUrl, data)
    urllib2.urlopen(request)

  def hipchat(self):
    if 'HIPCHAT_AUTH_TOKEN' not in current_app.config:
      return False

    if 'HIPCHAT_ROOM' not in current_app.config:
      return False

    authToken = current_app.config['HIPCHAT_AUTH_TOKEN']
    room = current_app.config['HIPCHAT_ROOM']
    siteUrl = current_app.config['SITE_URL']

    if not authToken or not room or not siteUrl:
      return False

    sender = 'ChalicePoints'
    if 'HIPCHAT_SENDER' in current_app.config:
      sender = current_app.config['HIPCHAT_SENDER']

    color = 'green'
    if 'HIPCHAT_COLOR' in current_app.config:
      color = current_app.config['HIPCHAT_COLOR']

    url = '%s/user/%s' % (siteUrl, self.target.id)
    points = 'Point' if self.amount == 1 else 'Points'
    message = '(chalicepoint) %s gave %s %d Chalice %s: %s - %s (%s)' % (self.source.name, self.target.name, self.amount, points, self.types[self.type], self.message, url)

    args = {
      'room_id': room,
      'message': message,
      'from': sender,
      'color': color,
      'message_format': 'text',
      'notice': 0,
    }

    data = urllib.urlencode(args)

    apiUrl = 'https://api.hipchat.com/v1/rooms/message?auth_token=%s' % (authToken)
    request = urllib2.Request(apiUrl, data)
    urllib2.urlopen(request)

  @staticmethod
  def get_points(type='all'):
    given = Event.select(Event, fn.Sum(Event.amount).alias('given'))
    given = given.group_by(Event.source)

    received = Event.select(Event, fn.Sum(Event.amount).alias('received'))
    received = received.group_by(Event.target)

    if type == 'week':
      now = datetime.now().date()
      dow = now.weekday()

      first_delta = timedelta(days=dow)
      first_day = now - first_delta

      last_delta = timedelta(days=6 - dow)
      last_day = now + last_delta

      given = given.where(fn.Date(Event.created_at) >= first_day, fn.Date(Event.created_at) <= last_day)
      received = received.where(fn.Date(Event.created_at) >= first_day, fn.Date(Event.created_at) <= last_day)
    elif type == 'month':
      now = datetime.now().date()
      first_day = now.replace(day=1)
      last_day = now.replace(day=monthrange(now.year, now.month)[1])

      given = given.where(fn.Date(Event.created_at) >= first_day, fn.Date(Event.created_at) <= last_day)
      received = received.where(fn.Date(Event.created_at) >= first_day, fn.Date(Event.created_at) <= last_day)

    totals = {}
    for event in given:
      if event.source.id not in totals:
        totals[event.source.id] = event.source
        totals[event.source.id].given = 0
        totals[event.source.id].received = 0

      totals[event.source.id].given = event.given

    for event in received:
      if event.target.id not in totals:
        totals[event.target.id] = event.target
        totals[event.target.id].given = 0
        totals[event.target.id].received = 0

      totals[event.target.id].received = event.received

    return totals
