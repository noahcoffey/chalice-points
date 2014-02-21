import os
import json
import urllib, urllib2

from datetime import datetime, timedelta

from flask import abort, jsonify, Response, current_app
from flask.ext.login import current_user

from peewee import *

import chalicepoints
from chalicepoints.models.base import BaseModel, BaseModelJSONEncoder as Encoder
from chalicepoints.models.user import User

class Event(BaseModel):
    source = ForeignKeyField(User, db_column='source', related_name='given')
    target = ForeignKeyField(User, db_column='target', related_name='received')
    amount = IntegerField()
    message = CharField()

    def add(self):
        self.save()
        self.hipchat()

    def hipchat(self):
        if 'HIPCHAT_AUTH_TOKEN' not in current_app.config:
            return False

        if 'HIPCHAT_ROOM' not in current_app.config:
            return False

        authToken = current_app.config['HIPCHAT_AUTH_TOKEN']
        room = current_app.config['HIPCHAT_ROOM']

        if not authToken or not room:
            return False

        sender = 'ChalicePoints'
        if 'HIPCHAT_SENDER' in current_app.config:
            sender = current_app.config['HIPCHAT_SENDER']

        color = 'green'
        if 'HIPCHAT_COLOR' in current_app.config:
            color = current_app.config['HIPCHAT_COLOR']

        url = 'http://chalicepoints.formstack.com/#/user/%s' % (self.target.id)
        points = 'Point' if self.amount == 1 else 'Points'
        message = '(chalicepoint) %s gave %s %d Chalice %s: %s (%s)' % (self.source.name, self.target.name, self.amount, points, self.message, url)

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
        result = urllib2.urlopen(request)

    @staticmethod
    def get_timeline():
        q = Event.select().order_by(Event.created_at.desc())

        timeline = []
        for event in q:
            event.source_user = User.get(User.id == event.source)
            event.target_user = User.get(User.id == event.target)

            timeline.append(event)

        return timeline

    @staticmethod
    def get_points(week=False):
        #q = Event.select()
        given = Event.select(Event, fn.Sum(Event.amount).alias('given'))
        given = given.group_by(Event.source)

        received = Event.select(Event, fn.Sum(Event.amount).alias('received'))
        received = received.group_by(Event.target)

        if week:
            now = datetime.now()
            dow = now.weekday()

            first_delta = timedelta(days=dow)
            first_day = now - first_delta

            last_delta = timedelta(days=6 - dow)
            last_day = now + last_delta

            given = given.where(Event.created_at >= first_day, Event.created_at <= last_day)
            received = received.where(Event.created_at >= first_day, Event.created_at <= last_day)

        totals = {}
        for event in given:
            if event.source.id not in totals:
                totals[event.source.id] = event.source
                totals[event.source.id].given = 0
                totals[event.source.id].received = 0

            totals[event.source.id].given = event.given;

        for event in received:
            if event.target.id not in totals:
                totals[event.target.id] = event.target
                totals[event.target.id].given = 0
                totals[event.target.id].received = 0

            totals[event.target.id].received = event.received;

        return totals
