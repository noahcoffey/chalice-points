import os
import json
from datetime import datetime
from ordereddict import OrderedDict

from flask import abort, jsonify
from flask.ext.login import current_user

import chalicepoints
from chalicepoints.models.base import BaseModel
from chalicepoints.models.user import User

class Event(BaseModel):
    @staticmethod
    def get_timeline():
        events = {}

        users = User.get_users()
        for name in users:
            user_events = Event.get_events(name)
            for event in user_events:
                if event['type'] != 'give':
                    continue

                timestamp = float(datetime.strptime(event['date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%s'))
                while timestamp in events:
                    timestamp += 0.001

                event['source'] = name
                events[timestamp] = event

        timeline = OrderedDict(sorted(events.items(), key=lambda t: -t[0]))

        return timeline

    @staticmethod
    def do_get_events():
        events = {}

        users = User.get_users()
        for name in users:
            events[name] = Event.get_events(name)

        return jsonify(success=1, events=events)

    @staticmethod
    def do_post_events(data):
        source = current_user.name
        target = data['target'].encode('ascii')
        amount = max(min(5, data['amount']), 1)

        if target == current_user.name:
            abort(403)

        users = User.get_user_names()
        if target not in users:
            abort(403)

        message = 'None'
        if 'message' in data and data['message']:
            message = data['message'].encode('ascii')

        eventDate = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        Event.add_event(source, target, eventDate, amount, message)

        return jsonify(success=1)

    @staticmethod
    def get_events(name, deleted=None):
        userKey = Event.to_key(name)
        eventsKey = 'cpEvents' + userKey

        events = []
        if chalicepoints.r.exists(eventsKey):
            eventsLen = chalicepoints.r.llen(eventsKey)
            for idx in range(eventsLen):
                eventJSON = chalicepoints.r.lindex(eventsKey, idx)
                event = json.loads(eventJSON)

                if not deleted and '__deleted' in event:
                    continue

                events.append(event)

        return events

    @staticmethod
    def add_event(source, target, eventDate, amount, message):
        if source == target:
            return False

        sourceKey = Event.to_key(source)
        givenKey = 'cpEvents' + sourceKey
        given = {
            'type': 'give',
            'user': target,
            'amount': amount,
            'date': eventDate,
            'message': message,
        }
        chalicepoints.r.lpush(givenKey, json.dumps(given))

        targetKey = Event.to_key(target)
        receivedKey = 'cpEvents' + targetKey
        received = {
            'type': 'receive',
            'user': source,
            'amount': amount,
            'date': eventDate,
            'message': message,
        }
        chalicepoints.r.lpush(receivedKey, json.dumps(received))

        Event.update_hipchat(source, target, amount, message)

    '''
    @staticmethod
    def remove_event(source, target, date):
        source = source.encode('ascii')
        target = target.encode('ascii')
        date = date.encode('ascii')

        found = False

        sourceEvents = Event.get_events(source)
        for idx in range(len(sourceEvents)):
            event = sourceEvents[idx]
            if event['user'] == target and event['date'] == date:
                found = True
                Event.set_deleted_flag(source, idx, event, True)

        targetEvents = Event.get_events(target)
        for idx in range(len(targetEvents)):
            event = targetEvents[idx]
            if event['user'] == source and event['date'] == date:
                found = True
                setDeletedFlag(source, idx, event, True)

        return found

    @staticmethod
    def set_deleted_flag(key, idx, event, deleted=True):
        if deleted:
            event['__deleted'] = 1
        else:
            event.pop('__deleted', None)

        chalicepoints.r.lset(key, idx, json.dumps(event))
    '''
