from flask import Flask, request, jsonify
from models import db, User, Todo, Message
from flask_socketio import SocketIO, send, emit
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db.init_app(app)
socketio = SocketIO(app)

# 소켓 이벤트 핸들러

@socketio.on('message')
def handle_message(data):
    # 메시지를 데이터베이스에 저장
    message = Message(sender_id=data['sender_id'], receiver_id=data['receiver_id'], content=data['content'])
    db.session.add(message)
    db.session.commit()
    # 모든 클라이언트에게 메시지 브로드캐스트
    emit('message', data, broadcast=True)

@app.route('/')
def home():
    return 

if __name__ == '__main__':
    socketio.run(app, debug=True)
