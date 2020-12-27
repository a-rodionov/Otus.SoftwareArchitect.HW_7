import os
import json
import hashlib

from flask import Flask, request
from flask_api import status
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, Email
from sqlalchemy import create_engine

class CreateUserForm(FlaskForm):
    username = StringField("username: ", validators=[DataRequired()])
    password = StringField("password: ", validators=[DataRequired()])
    firstName = StringField("firstName: ", validators=[DataRequired()])
    lastName = StringField("lastName: ", validators=[DataRequired()])
    email = StringField("email: ", validators=[Email()])
    phone = StringField("phone: ", validators=[DataRequired()])

class MoneyTransactionForm(FlaskForm):
    amount = IntegerField("amount: ", validators=[DataRequired()])

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


@app.route('/billing/user', methods=['POST'])
def user_create():
    try:
        createUserForm = CreateUserForm(meta={'csrf': False})
        if createUserForm.validate():
            engine = create_engine(config['DATABASE_URI'], echo=True)
            with engine.connect() as connection:
                salt = os.urandom(32)
                password = hashlib.pbkdf2_hmac('sha256', createUserForm.password.data.encode('utf-8'), salt, 100000, dklen=128)
                result = connection.execute('''insert into users (username, password, firstName, lastName, email, phone) values(%s, %s, %s, %s, %s, %s) returning id''',
                                            (createUserForm.username.data,
                                             salt + password,
                                             createUserForm.firstName.data,
                                             createUserForm.lastName.data,
                                             createUserForm.email.data,
                                             createUserForm.phone.data))
                userId = result.scalar()
                if userId is None:
                    return '', status.HTTP_400_BAD_REQUEST
                else:
                    return json.dumps({'userId': userId}), status.HTTP_201_CREATED
        else:
            return json.dumps({'code': ERROR_INPUT_DATA, 'message': str(createUserForm.errors)}), status.HTTP_400_BAD_REQUEST
    except Exception as exc:
        return json.dumps({'code': ERROR_UNEXPECTED, 'message': str(exc)}), status.HTTP_500_INTERNAL_SERVER_ERROR


@app.route('/billing/user/<int:userId>', methods=['GET'])
def user_get(userId):
    try:
        engine = create_engine(config['DATABASE_URI'], echo=True)
        rows = []
        with engine.connect() as connection:
            result = connection.execute('''select id, username, firstName, lastName, email, phone, balance from users where id = %s''', userId)
            row = result.first()
            if row is None:
                return '', status.HTTP_404_NOT_FOUND
            else:
                return json.dumps(dict(row.items())), status.HTTP_200_OK
    except Exception as exc:
        return json.dumps({'code': ERROR_UNEXPECTED, 'message': str(exc)}), status.HTTP_500_INTERNAL_SERVER_ERROR

@app.route('/billing/deposit/<int:userId>', methods=['POST'])
def deposit(userId):
    try:
        moneyTransactionForm = MoneyTransactionForm(meta={'csrf': False})
        if moneyTransactionForm.validate():
            engine = create_engine(config['DATABASE_URI'], echo=True)
            with engine.connect() as connection:
                result = connection.execute('''update users set balance = balance + %s::bigint where id = %s returning id''',
                                            (moneyTransactionForm.amount.data,
                                             userId))
                userId = result.scalar()
                if userId is None:
                    return '', status.HTTP_404_NOT_FOUND
                else:
                    return '', status.HTTP_200_OK
        else:
            return json.dumps({'code': ERROR_INPUT_DATA, 'message': str(moneyTransactionForm.errors)}), status.HTTP_400_BAD_REQUEST
    except Exception as exc:
        return json.dumps({'code': ERROR_UNEXPECTED, 'message': str(exc)}), status.HTTP_500_INTERNAL_SERVER_ERROR

@app.route('/billing/withdraw/<int:userId>', methods=['POST'])
def withdraw(userId):
    try:
        moneyTransactionForm = MoneyTransactionForm(meta={'csrf': False})
        if moneyTransactionForm.validate():
            engine = create_engine(config['DATABASE_URI'], echo=True)
            with engine.connect() as connection:
                result = connection.execute('''select balance from users where id = %s''', userId)
                balance = result.scalar()
                if balance is None:
                    return '', status.HTTP_404_NOT_FOUND
                if balance < moneyTransactionForm.amount.data:
                    return '', status.HTTP_412_PRECONDITION_FAILED
                result = connection.execute('''update users set balance = balance - %s::bigint where id = %s returning id''',
                                            (moneyTransactionForm.amount.data,
                                             userId))
                userId = result.scalar()
                if userId is None:
                    return '', status.HTTP_500_INTERNAL_SERVER_ERROR
                else:
                    return '', status.HTTP_200_OK
        else:
            return json.dumps({'code': ERROR_INPUT_DATA, 'message': str(moneyTransactionForm.errors)}), status.HTTP_400_BAD_REQUEST
    except Exception as exc:
        return json.dumps({'code': ERROR_UNEXPECTED, 'message': str(exc)}), status.HTTP_500_INTERNAL_SERVER_ERROR

if __name__ == "__main__":
    app.run(host='0.0.0.0',port='8000')