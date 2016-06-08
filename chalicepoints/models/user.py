import simplejson as json

from flask import current_app
from flask.ext.login import UserMixin, current_user
from peewee import *
from playhouse.shortcuts import model_to_dict

import chalicepoints
from chalicepoints.models.base import BaseModel, BaseModelJSONEncoder

class User(BaseModel, UserMixin):
  name = CharField()
  email = CharField()
  gravatar = CharField()
  max_points = IntegerField()
  disabled = BooleanField(default=False)
  url = CharField()
  settings = TextField()
  elder = BooleanField(default=False)

  def to_array(self, for_public=False):
    data = super(User, self).to_array()

    data['settings'] = self.get_settings()

    if for_public:
      data.pop('url', None)

    return data

  def to_json(self, for_public=False):
    data = self.to_array(for_public)
    return json.dumps(data, cls=UserModelJSONEncoder)

  def get_settings(self):
    if self.settings is None or len(self.settings) == 0:
      return {}

    try:
      settings = json.loads(self.settings)
    except ValueError:
      settings = {}

    return settings

  def get_timeline(self):
    from chalicepoints.models.event import Event

    query = Event.select()
    query = query.where((Event.source == self.id) | (Event.target == self.id))
    query = query.order_by(Event.created_at.desc())

    timeline = []

    for event in query:
      if event.target.id == self.id:
        event.type = 'receive'
      else:
        event.type = 'give'

      timeline.append(event)

    return timeline

  @staticmethod
  def get_digest_weekly():
    query = User.select()
    query = query.where(User.settings % '%%"weekly": true%%')

    users = []
    for user in query:
      users.append((user.name, user.email))

    return users

  @staticmethod
  def get_digest_monthly():
    query = User.select()
    query = query.where(User.settings % '%%"monthly": true%%')

    users = []
    for user in query:
      users.append((user.name, user.email))

    return users

  @staticmethod
  def get_user(user_id, include_points=False):
    from chalicepoints.models.event import Event

    given_query = Event.select(Event.target, fn.Sum(Event.amount).alias('total')).group_by(Event.target).alias('GIVEN')
    received_query = Event.select(Event.source, fn.Sum(Event.amount).alias('total')).group_by(Event.source).alias('RECEIVED')

    query = User.select()

    if include_points:
      query = User.select(User, given_query.c.total.alias('given'), received_query.c.total.alias('received'))

      query = query.join(
        given_query, on=(User.id == given_query.c.target)
      ).switch(User).join(
        received_query, on=(User.id == received_query.c.source)
      ).switch(User)

    query = query.where(User.id == user_id)

    return query.get()

  @staticmethod
  def get_users(include_self=True, include_points=False, exclude_disabled=False):
    from chalicepoints.models.event import Event

    given_query = Event.select(Event.target, fn.Sum(Event.amount).alias('total')).group_by(Event.target).alias('GIVEN')
    received_query = Event.select(Event.source, fn.Sum(Event.amount).alias('total')).group_by(Event.source).alias('RECEIVED')

    query = User.select()

    if include_points:
      query = User.select(User, given_query.c.total.alias('given'), received_query.c.total.alias('received'))

      query = query.join(
        given_query, on=(User.id == given_query.c.target)
      ).switch(User).join(
        received_query, on=(User.id == received_query.c.source)
      ).switch(User)

    if not include_self:
      query = query.where(User.id != current_user.id)

    if exclude_disabled:
      query = query.where(User.disabled == False)

    query = query.order_by(User.name.desc())

    users = []

    for user in query:
      users.append(user)

    return users

class UserModelJSONEncoder(BaseModelJSONEncoder):
  def default(self, obj):
    if isinstance(obj, User):
      return obj.to_array(for_public=True)
    else:
      return super(UserModelJSONEncoder, self).default(obj)
