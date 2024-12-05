# app.py

from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from models import db, Task
from datetime import datetime
from forms import TaskForm
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)

# Флаг для проверки, создавались ли таблицы
tables_created = False

# Настройки для Google API
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

@app.before_request
def create_tables():
    global tables_created
    if not tables_created:
        db.create_all()
        tables_created = True

@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_completed = True
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/')
def index():
    form = TaskForm()
    category_filter = request.args.get('category', '')
    priority_filter = request.args.get('priority', '')
    status_filter = request.args.get('status', '')

    query = Task.query
    if category_filter:
        query = query.filter_by(category=category_filter)
    if priority_filter:
        query = query.filter_by(priority=int(priority_filter))
    if status_filter == 'completed':
        query = query.filter_by(is_completed=True)
    elif status_filter == 'incomplete':
        query = query.filter_by(is_completed=False)

    tasks = query.all()
    return render_template('index.html', form=form, tasks=tasks, category_filter=category_filter, priority_filter=priority_filter, status_filter=status_filter)

@app.route('/add_task', methods=['POST'])
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            priority=form.priority.data,
            start_date=form.start_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data
        )
        db.session.add(task)
        db.session.commit()
        add_event_to_google_calendar(task)
        return redirect(url_for('index'))
    return redirect(url_for('index'))

def add_event_to_google_calendar(task):
    if 'credentials' not in session:
        return redirect('authorize')

    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    event = {
        'summary': task.title,
        'description': task.description,
        'start': {
            'dateTime': f"{task.start_date}T{task.start_time}",
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': f"{task.start_date}T{task.end_time}",
            'timeZone': 'UTC',
        },
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    task.google_event_id = created_event['id']
    db.session.commit()

def update_event_in_google_calendar(task):
    if 'credentials' not in session:
        return redirect('authorize')

    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    event = service.events().get(calendarId='primary', eventId=task.google_event_id).execute()

    event['summary'] = task.title
    event['description'] = task.description
    event['start'] = {
        'dateTime': f"{task.start_date}T{task.start_time}",
        'timeZone': 'UTC',
    }
    event['end'] = {
        'dateTime': f"{task.start_date}T{task.end_time}",
        'timeZone': 'UTC',
    }

    updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.category = form.category.data
        task.priority = form.priority.data
        task.start_date = form.start_date.data
        task.start_time = form.start_time.data
        task.end_time = form.end_time.data
        db.session.commit()
        update_event_in_google_calendar(task)
        return redirect(url_for('index'))
    return render_template('edit_task.html', form=form, task=task)

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if 'credentials' in session:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
        service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
        service.events().delete(calendarId='primary', eventId=task.google_event_id).execute()
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/authorize')
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    return redirect(url_for('index'))

def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

if __name__ == '__main__':
    app.run(debug=True)