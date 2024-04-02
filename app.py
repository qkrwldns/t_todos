from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_login import login_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
bootstrap = Bootstrap(app)

# 나머지 코드...

@app.route('/login', methods=['GET', 'POST'])
def login():
    if form.validate_on_submit():
        # 사용자 검증 로직 (해시 사용하지 않음)
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password')
    return render_template('login.html', title='Login')
