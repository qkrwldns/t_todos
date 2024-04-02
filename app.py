from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from models import db, Users, Todos, Msg
from flask_socketio import SocketIO, send, emit
import os
from dotenv import load_dotenv
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import LoginForm, RegisterForm, CommentForm
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db.init_app(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)

# 소켓 이벤트 핸들러

# @socketio.on('message')
# def handle_message(data):
#     # 메시지를 데이터베이스에 저장
#     message = Message(sender_id=data['sender_id'], receiver_id=data['receiver_id'], content=data['content'])
#     db.session.add(message)
#     db.session.commit()
#     # 모든 클라이언트에게 메시지 브로드캐스트
#     emit('message', data, broadcast=True)

@app.route('/')
@login_required
def main_page():
    if current_user.id == 1:
        # 관리자 권한 부여 로직
        pass
    # 메인 페이지 렌더링
    return render_template('main_page.html')

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_page')) # 메인 페이지로 리디렉션

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main_page')) # 로그인 성공 시 메인 페이지로 리디렉션
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

if __name__ == '__main__':
    socketio.run(app, debug=True)
