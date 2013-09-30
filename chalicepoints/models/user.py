import json

from flask.ext.login import UserMixin

import chalicepoints
from chalicepoints.models.base import BaseModel

class User(BaseModel, UserMixin):
    def __init__(self, user):
        self.email = user['email']
        self.name = user['name']
        self.gravatar = user['gravatar']
        self.max_points = user['max_points']
        self.disabled = user['disabled']

    def set_id(self, url):
        self.url = url

    def get_id(self):
        return self.url

    def to_json(self, for_public=False):
        d = {
            'email': self.email,
            'name' : self.name,
            'gravatar': self.gravatar,
            'max_points': self.max_points,
            'disabled': self.disabled,
        }

        if not for_public:
            d['url'] = self.url

        return json.dumps(d)

    @staticmethod
    def get_instance(email):
        user_dict = User.get_user_by_email(email)
        if not user_dict:
            return None

        user = User(user_dict)
        return user

    @staticmethod
    def get_user_dict():
        users_key = 'cpUsers'

        user_dict = None
        if chalicepoints.r.exists(users_key):
            user_dict = chalicepoints.r.hgetall(users_key)

        return user_dict

    @staticmethod
    def get_user_names():
        names = []

        user_dict = User.get_user_dict()
        if user_dict != None:
            for user_key in user_dict:
                user_json = user_dict[user_key]
                user = json.loads(user_json)
                names.append(user['name'])

        return names

    @staticmethod
    def get_user_emails():
        emails = {}
        user_dict = User.get_user_dict()
        if user_dict != None:
            for user_key in user_dict:
                user_json = user_dict[user_key]
                user = json.loads(user_json)
                emails[user['email']] = user['name']

        return emails

    @staticmethod
    def get_users():
        users = {}

        user_dict = User.get_user_dict()
        if user_dict != None:
            for user_key in user_dict:
                user_json = user_dict[user_key]
                user = json.loads(user_json)
                users[user['name']] = user

        return users

    @staticmethod
    def get_user(name):
        user_key = User.to_key(name)

        user = None
        if chalicepoints.r.hexists('cpUsers', user_key):
            user_json = chalicepoints.r.hget('cpUsers', user_key)
            user = json.loads(user_json)

        return user

    @staticmethod
    def get_user_by_email(email):
        user = None
        user_dict = User.get_user_dict()
        if user_dict != None:
            for user_key in user_dict:
                user_json = user_dict[user_key]
                user_obj = json.loads(user_json)
                if user_obj['email'] == email:
                    user = user_obj

        return user
