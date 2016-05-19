import os, string
import simplejson as json
from flask import current_app
from peewee import *
from chalicepoints import db
import datetime

class BaseModel(db.Model):
    created_at =  DateTimeField()
    updated_at =  DateTimeField()

    def before_save(self):
        now = datetime.datetime.now()

        if self.created_at is None:
            self.created_at = now

        self.updated_at = now

    def save(self):
        self.before_save()
        res = super(BaseModel, self).save()
        return res

    def to_array(self):
        props = dict((key, getattr(self, key)) for key in dir(self) if key not in dir(self.__class__) and not key.startswith('_'))
        data = self.__dict__.get('_data')

        return dict(data.items() + props.items())

    def to_json(self):
        return json.dumps(self.to_array(), cls=BaseModelJSONEncoder)

class DateTimeEncoder(json.JSONEncoder):
    """Adds datetime support to the JSONEncoder.
    Modified  from http://stackoverflow.com/a/12126976/1638
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        else:
            return super(DateTimeEncoder, self).default(obj)

class BaseModelJSONEncoder(DateTimeEncoder):
    """Adds BaseModel support to the JSONEncoder"""
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.to_array()
        else:
            return super(BaseModelJSONEncoder, self).default(obj)
