import json
from datetime import datetime

from chalicepoints.models.base import BaseModel
from chalicepoints.models.user import User
from chalicepoints.models.event import Event

class Point(BaseModel):
    @staticmethod
    def get_points(week=False):
        points = {}

        users = User.get_users()
        for source in users:
            sourceUser = users[source]
            if not sourceUser:
                continue

            if sourceUser['disabled']:
                continue

            events = Event.get_events(source, False, week)
            for event in events:
                target = event['user']
                targetUser = User.get_user(target)
                if not targetUser:
                    continue

                if targetUser['disabled']:
                    continue

                if source not in points:
                    points[source] = {
                        'givenTotal': 0,
                        'receivedTotal': 0,
                        'given': {},
                        'received': {},
                    }

                amount = int(event['amount'])

                if event['type'] == 'give':
                    points[source]['givenTotal'] += amount

                    if target not in points[source]['given']:
                        points[source]['given'][target] = 0

                    points[source]['given'][target] += amount
                else:
                    points[source]['receivedTotal'] += amount

                    if target not in points[source]['received']:
                        points[source]['received'][target] = 0

                    points[source]['received'][target] += amount

        return points
