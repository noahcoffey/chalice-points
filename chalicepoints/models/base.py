import os, string
import urllib, urllib2

class BaseModel():
    @staticmethod
    def to_key(name):
        name = name.encode('ascii')
        key = string.translate(name, None, ' ')
        key = string.translate(key, None, '-')

        return key

    @staticmethod
    def update_hipchat(giver, receiver, amount, message):
        authToken = os.getenv('HIPCHAT_AUTH_TOKEN', None)
        room = os.getenv('HIPCHAT_ROOM', None)

        if not authToken or not room:
            return False

        sender = os.getenv('HIPCHAT_SENDER', 'ChalicePoints')
        color = os.getenv('HIPCHAT_COLOR', 'green')
        msgFormat = os.getenv('HIPCHAT_FORMAT', 'text')

        url = 'http://chalicepoints.formstack.com/#/user/%s' % (urllib.quote(receiver))
        points = 'Point' if amount == 1 else 'Points'
        message = '(chalicepoint) %s gave %s %d Chalice %s: %s (%s)' % (giver, receiver, amount, points, message, url)

        args = {
            'room_id': room,
            'message': message,
            'from': sender,
            'color': color,
            'message_format': msgFormat,
            'notice': 0,
        }

        data = urllib.urlencode(args)

        apiUrl = 'https://api.hipchat.com/v1/rooms/message?auth_token=%s' % (authToken)
        request = urllib2.Request(apiUrl, data)
        result = urllib2.urlopen(request)
