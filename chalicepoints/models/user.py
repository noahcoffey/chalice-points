import json

from flask.ext.login import UserMixin

import chalicepoints
from chalicepoints.models.base import BaseModel

class User(BaseModel, UserMixin):
    def __init__(self, url, email, name):
        self.url = url
        self.email = email
        self.name = name

    def get_id(self):
        return self.url

    def to_json(self, for_public=False):
        d = {
            'email': self.email,
            'name' : self.name,
        }

        if not for_public:
            d['url'] = self.url

        return json.dumps(d)

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
