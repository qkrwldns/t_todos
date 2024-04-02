from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = os.getenv('PASSWORD')
app.config['MYSQL_DB'] = 't_todos'

Bootstrap(app)
mysql = MySQL(app)

class LoginForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

@app.route('/', methods=['GET', 'POST'])
def index():
    login_form = LoginForm()
    register_form = RegisterForm()
    if login_form.validate_on_submit():
        # 로그인 검증 로직
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE Username=%s AND Password=%s',
            (login_form.username.data, login_form.password.data)
        )
        user = cursor.fetchone()
        cursor.close()
        if user:
            # 세션 생성 및 메인 페이지로 리다이렉트
            return redirect(url_for('main'))
        else:
            # 로그인 실패
            flash('Invalid username or password')
    elif register_form.validate_on_submit():
        # 회원가입 로직
        cursor = mysql.connection.cursor()
        cursor.execute(
            'INSERT INTO users (Username, Password) VALUES (%s, %s)',
            (register_form.username.data, register_form.password.data)
        )
        mysql.connection.commit()
        cursor.close()
        flash('Registration successful! Please login.')
        return redirect(url_for('index'))
    return render_template('index.html', login_form=login_form, register_form=register_form)

@app.route('/main')
def main():
    # 메인 페이지 로직
    return render_template('main.html')


if __name__ == '__main__':
    app.run(debug=True)
