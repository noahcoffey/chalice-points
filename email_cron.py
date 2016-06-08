import os, sys, string
import simplejson as json
from datetime import datetime, timedelta, time

from flask import Flask, render_template

from flask.ext.script import Manager
from flask.ext.mail import Mail, Message

from flask_peewee.db import Database
from peewee import MySQLDatabase, DoesNotExist

from chalicepoints import app
from chalicepoints.models.user import User
from chalicepoints.models.event import Event

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'chalicepoints')
app = Flask(__name__, template_folder='chalicepoints/templates', static_folder=os.path.join(PROJECT_ROOT, 'public'), static_url_path='/public')

app.config.from_object('chalicepoints.config.DefaultConfig')
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY', app.config['SECRET_KEY'])

manager = Manager(app)
mail = Mail(app)

@manager.command
def digest_weekly():
  history = Event.select()

  now = datetime.now().date()
  dow = now.weekday()

  start_delta = timedelta(days=dow)
  start_date = now - start_delta
  start_text = start_date.strftime('%b %-d, %Y')

  end_delta = timedelta(days=6 - dow)
  end_date = now + end_delta
  end_text = end_date.strftime('%b %-d, %Y')

  history = history.where(Event.created_at >= start_date)
  history = history.where(Event.created_at <= end_date)
  history = history.order_by(Event.created_at.desc())

  events = []
  for event in history:
    event.type = Event.types[event.type]
    events.append(event)

  recipients = User.get_digest_weekly()

  text_body = render_template('digest_weekly.txt', events=events, start_date=start_text, end_date=end_text, base_url=app.config['SITE_URL'])
  html_body = render_template('digest_weekly.html', events=events, start_date=start_text, end_date=end_text, base_url=app.config['SITE_URL'])

  send_email('[CHALICEPOINTS] Weekly Digest', ('Chalice Points', app.config['SENDER_EMAIL']), recipients, text_body, html_body, ('Chalice Points', app.config['REPLY_EMAIL']))

@manager.command
def digest_monthly():
  history = Event.select()

  now = datetime.now().date()

  start_date = now.replace(day = 1)
  start_text = start_date.strftime('%b %-d, %Y')

  end_date = now.replace(day = monthrange(now.year, now.month)[1])
  end_text = end_date.strftime('%b %-d, %Y')

  history = history.where(Event.created_at >= start_date)
  history = history.where(Event.created_at <= end_date)
  history = history.order_by(Event.created_at.desc())

  events = []
  for event in history:
    event.type = Event.types[event.type]
    events.append(event)

  recipients = User.get_digest_monthly()

  text_body = render_template('digest_monthly.txt', events=events, start_date=start_text, end_date=end_text, base_url=app.config['SITE_URL'])
  html_body = render_template('digest_monthly.html', events=events, start_date=start_text, end_date=end_text, base_url=app.config['SITE_URL'])

  send_email('[CHALICEPOINTS] Monthly Digest', ('Chalice Points', app.config['SENDER_EMAIL']), recipients, text_body, html_body, ('Chalice Points', app.config['REPLY_EMAIL']))


def send_email(subject, sender, recipients, text_body, html_body, reply_to):
  msg = Message(subject, sender=sender, bcc=recipients, reply_to=reply_to)
  msg.body = text_body
  msg.html = html_body

  with app.app_context():
    mail.send(msg)

if __name__ == '__main__':
  manager.run()
