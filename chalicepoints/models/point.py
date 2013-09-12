import json
from datetime import datetime

from chalicepoints.models.base import BaseModel
from chalicepoints.models.user import User
from chalicepoints.models.event import Event

class Point(BaseModel):
    @staticmethod
    def get_points():
        points = {}

        users = User.get_users()
        for source in users:
            if source not in points:
                points[source] = {
                    'givenTotal': 0,
                    'receivedTotal': 0,
                    'given': {},
                    'received': {},
                }

            events = Event.get_events(source)
            for event in events:
                target = event['user']
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

    @staticmethod
    def get_points_by_week():
        points = {}

        users = User.get_users()
        for source in users:
            events = Event.get_events(source)
            for event in events:
                target = event['user']
                amount = int(event['amount'])

                week = datetime.strptime(event['date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%U %y 0')
                date = datetime.strptime(week, '%U %y %w').strftime('%Y-%m-%dT%H:%M:%SZ')

                if date not in points:
                    points[date] = {}

                if source not in points[date]:
                    points[date][source] = {
                        'givenTotal': 0,
                        'receivedTotal': 0,
                        'given': {},
                        'received': {},
                    }

                if event['type'] == 'give':
                    points[date][source]['givenTotal'] += amount

                    if target not in points[date][source]['given']:
                        points[date][source]['given'][target] = 0

                    points[date][source]['given'][target] += amount
                else:
                    points[date][source]['receivedTotal'] += amount

                    if target not in points[date][source]['received']:
                        points[date][source]['received'][target] = 0

                    points[date][source]['received'][target] += amount

        return points
