import json

from flask.ext.login import UserMixin, current_user
from peewee import *

import chalicepoints
from chalicepoints.models.base import BaseModel, BaseModelJSONEncoder

class User(BaseModel, UserMixin):
    name = CharField()
    email = CharField()
    gravatar = CharField()
    max_points = IntegerField()
    disabled = BooleanField(default=False)
    url = CharField()

    def to_array(self, for_public=False):
        data = super(User, self).to_array()
        if for_public:
            data.pop('url', None)

        return data

    def to_json(self, for_public=False):
        data = self.to_array(for_public)
        return json.dumps(data, cls=UserModelJSONEncoder)

    def get_given(self):
        return [event for event in self.given]

    def get_received(self):
        return [event for event in self.received]

    def get_timeline(self):
        from chalicepoints.models.event import Event

        q = Event.select()
        q = q.where((Event.source == self.id) | (Event.target == self.id))
        q = q.order_by(Event.created_at.desc())

        timeline = []
        for event in q:
            if event.target.id == self.id:
                event.type = 'receive'
            else:
                event.type = 'give'

            event.source_user = User.get(User.id == event.source)
            event.target_user = User.get(User.id == event.target)

            timeline.append(event)

        return timeline

    def get_points(self, week=False):
        from chalicepoints.models.event import Event

        given_query = Event.select(fn.Sum(Event.amount).alias('total'))
        given_query = given_query.where(Event.source == self.id)

        received_query = Event.select(fn.Sum(Event.amount).alias('total'))
        received_query = received_query.where(Event.target == self.id)

        if type == 'week':
            now = datetime.now()
            dow = now.weekday()

            first_delta = timedelta(days=dow)
            first_day = now - first_delta

            last_delta = timedelta(days=6 - dow)
            last_day = now + last_delta

            given_query = given_query.where(Event.created_at >= first_day, Event.created_at <= last_day)
            received_query = received_query.where(Event.created_at >= first_day, Event.created_at <= last_day)

        given = given_query.get()
        received = received_query.get()

        return {
            'given': given.total or 0,
            'received': received.total or 0
        }

    @staticmethod
    def get_users(include_self=True):
        q = User.select()
        if not include_self:
            q = q.where(User.id != current_user.id)

        return [user for user in q]

class UserModelJSONEncoder(BaseModelJSONEncoder):
    def default(self, obj):
        if isinstance(obj, User):
            return obj.to_array(for_public=True)
        else:
            return super(UserModelJSONEncoder, self).default(obj)
