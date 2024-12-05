from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SubmitField,DateField,TimeField, SelectField
from wtforms.validators import DataRequired

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    category = SelectField('Category', choices=[('work', 'Работа'), ('personal', 'Личные дела'), ('study', 'Учёба')])
    priority = SelectField('Priority', choices=[(1, 'Низкий'), (2, 'Средний'), (3, 'Высокий')])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    start_time = TimeField('Start Time', format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('End Time', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Add Task')
