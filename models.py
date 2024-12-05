from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    google_event_id = db.Column(db.String(255), nullable=True)  # Добавлено поле для хранения идентификатора события Google Calendar
    is_completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Task {self.title}>'