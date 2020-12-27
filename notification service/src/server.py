import os
import json

from flask import Flask, request
from flask_api import status
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Email
from sqlalchemy import create_engine

class EmailNotificationForm(FlaskForm):
    email = StringField("email: ", validators=[Email()])
    title = StringField("title: ", validators=[DataRequired()])
    message = StringField("message: ", validators=[DataRequired()])

app = Flask(__name__)

ERROR_UNEXPECTED = 1
ERROR_INPUT_DATA = 2
ERROR_OBJECT_NOT_FOUND = 3

config = {
    'DATABASE_URI': os.environ.get('DATABASE_URI', ''),
    'HOSTNAME': os.environ['HOSTNAME'],
    'APP_NAME': os.environ.get('APP_NAME', 'no name'),
}

@app.route("/")
def hello():
    return 'Application \'' + config['APP_NAME'] + '\' from ' + config['HOSTNAME'] + '!'

@app.route("/health")
def health():
    return '{"status": "ok"}'

@app.route("/config")
def configuration():
    return json.dumps(config)

@app.route('/notification/email/<int:userId>', methods=['POST'])
def send_email(userId):
    try:
        emailNotificationForm = EmailNotificationForm(meta={'csrf': False})
        if emailNotificationForm.validate():
            engine = create_engine(config['DATABASE_URI'], echo=True)
            with engine.connect() as connection:
                result = connection.execute('''insert into email (userId, email, title, message) values(%s, %s, %s, %s) returning userId''',
                                            (userId,
                                             emailNotificationForm.email.data,
                                             emailNotificationForm.title.data,
                                             emailNotificationForm.message.data))
                userId = result.scalar()
                if userId is None:
                    return '', status.HTTP_400_BAD_REQUEST
                else:
                    return '', status.HTTP_202_ACCEPTED
        else:
            return json.dumps({'code': ERROR_INPUT_DATA, 'message': str(emailNotificationForm.errors)}), status.HTTP_400_BAD_REQUEST
    except Exception as exc:
        return json.dumps({'code': ERROR_UNEXPECTED, 'message': str(exc)}), status.HTTP_500_INTERNAL_SERVER_ERROR

@app.route('/notification/email/<int:userId>', methods=['GET'])
def get_emails(userId):
    try:
        engine = create_engine(config['DATABASE_URI'], echo=True)
        rows = []
        with engine.connect() as connection:
            result = connection.execute('''select email, title, message from email where userId = %s''', userId)
            rows = [dict(r.items()) for r in result]
        return json.dumps(rows), status.HTTP_200_OK
    except Exception as exc:
        return json.dumps({'code': ERROR_UNEXPECTED, 'message': str(exc)}), status.HTTP_500_INTERNAL_SERVER_ERROR

if __name__ == "__main__":
    app.run(host='0.0.0.0',port='8000')