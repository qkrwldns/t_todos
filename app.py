from flask import Flask, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import os
from dotenv import load_dotenv
from flask_bootstrap import Bootstrap
from forms import LoginForm, RegisterForm  # forms.py에 정의된 WTForms 폼

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = 't_todos'
mysql = MySQL(app)
app.config['TEMPLATES_AUTO_RELOAD'] = True

login_manager = LoginManager()
login_manager.init_app(app)
Bootstrap(app)

# Flask-Login의 사용자 로더 설정
@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT UserID, Username, TeamID FROM Users WHERE UserID = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    
    if user_data:
        user = User(user_data[0], user_data[1], user_data[2])  # Assuming the third column is TeamID
        return user
    return None

class User(UserMixin):
    def __init__(self, id, username, team_id=None):
        self.id = str(id)
        self.username = username
        self.team_id = team_id


@app.route('/', methods=['GET', 'POST'])
def login_or_register():
    # 현재 사용자가 이미 로그인한 경우 홈 페이지로 리디렉션
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'login':
            username = request.form['username']
            password = request.form['password']
            cursor = mysql.connection.cursor()
    
            # 먼저 username으로 사용자 조회
            cursor.execute('SELECT * FROM Users WHERE Username = %s', (username,))
            user_data = cursor.fetchone()
            if user_data:
                # 사용자가 존재하면 비밀번호 비교
                # 2열은 비번
                if str(password) == str(user_data[2]):
                    # 비밀번호가 일치하면 로그인 처리
                    user = User(user_data[0], user_data[1])  # 첫 번째 컬럼이 UserID
                    login_user(user)
                    session['username'] = username
                    return redirect(url_for('home'))
                else:
                    # 비밀번호 불일치
                    flash('Incorrect password. Please try again.', 'danger')
            else:
                # 사용자가 존재하지 않음
                flash('No account found with that username. Please sign up.', 'danger')
        elif action == 'register':
            username = request.form['username']
            password = request.form['password']
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO Users (Username, Password) VALUES (%s, %s)', (username, password))
            mysql.connection.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login_or_register'))

    return render_template('index.html')
# 로그아웃 라우트
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login_or_register'))


# 홈 라우트
@app.route('/home')
@login_required
def home():
    cursor = mysql.connection.cursor()

    # 현재 로그인한 사용자의 정보를 불러오기
    cursor.execute("SELECT TeamID FROM Users WHERE UserID = %s", (current_user.id,))
    user_info = cursor.fetchone()
    cursor.close()

    # User 정보가 존재하고 TeamID가 1인 경우에만 todos를 불러오기
    if user_info and user_info[0] == 1:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT TodoID, UserID, Title, IsCompleted FROM Todos WHERE UserID = %s", (current_user.id,))
        todos_tuples = cursor.fetchall()
        cursor.close()

        # Convert tuples to dictionaries
        todos = [
            {'TodoID': todo[0], 'UserID': todo[1], 'Title': todo[2], 'IsCompleted': todo[3]}
            for todo in todos_tuples
        ]
        return render_template('home.html', name=current_user.username, todos=todos)
    
    # TeamID가 1이 아닌 경우 또는 user_info가 없는 경우 메시지 표시
    return render_template('home.html', name=current_user.username, message="You don't have permission to view these todos.")

# todo 추가 라우트
@app.route('/add_todo', methods=['POST'])
@login_required
def add_todo():
    title = request.form.get('title')
    if title:
        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO Todos (UserID, Title, IsCompleted) VALUES (%s, %s, %s)",
            (current_user.id, title, False)
        )
        mysql.connection.commit()
        cursor.close()  # Close the cursor after operation
    return redirect(url_for('home'))


# todo 토글로 완료 // 미완료 
@app.route('/toggle_todo/<int:todo_id>', methods=['POST'])
@login_required
def toggle_todo(todo_id):
    # Convert the checkbox 'on' or None to True/False
    is_completed = request.form.get('is_completed') == 'on'
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE Todos SET IsCompleted = %s WHERE TodoID = %s AND UserID = %s",
        (is_completed, todo_id, current_user.id)
    )
    mysql.connection.commit()
    cursor.close()  # Close the cursor after operation
    return redirect(url_for('home'))

# todo 삭제 라우트
@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
@login_required
def delete_todo(todo_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM Todos WHERE TodoID = %s AND UserID = %s", (todo_id, current_user.id))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('home'))

# todo 편집 글 불러오기 라우트
@app.route('/edit_todo/<int:todo_id>')
@login_required
def edit_todo(todo_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT TodoID, UserID, Title, IsCompleted FROM Todos WHERE TodoID = %s AND UserID = %s", (todo_id, current_user.id))
    todo_tuple = cursor.fetchone()
    cursor.close()

    if todo_tuple:
        # Convert the tuple to a dictionary
        todo = {
            'TodoID': todo_tuple[0],
            'UserID': todo_tuple[1],
            'Title': todo_tuple[2],
            'IsCompleted': todo_tuple[3]
        }
        return render_template('edit_todo.html', todo=todo)
    else:
        flash('Todo item not found.')
        return redirect(url_for('home'))

 # todo 실질적 편집 후 추가 라우트   
@app.route('/update_todo/<int:todo_id>', methods=['POST'])
@login_required
def update_todo(todo_id):
    title = request.form.get('title')
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE Todos SET Title = %s WHERE TodoID = %s AND UserID = %s", (title, todo_id, current_user.id))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('home'))

# 팀 -----------------------------------------------------------------------

# 팀 라우트
@app.route('/team')
@login_required
def team():
    if current_user.team_id is None:
        flash("You are not assigned to a team.")
        return redirect(url_for('home'))

    cursor = mysql.connection.cursor()
    # 현재 사용자와 같은 TeamID를 가진 사용자들의 정보 및 프로필 사진을 가져옵니다.
    cursor.execute("SELECT UserID, Username, ProfilePic FROM Users WHERE TeamID = %s", (current_user.team_id,))
    team_members_tuples = cursor.fetchall()

    # 현재 사용자를 제외한 팀 멤버 목록을 생성합니다.
    team_members = [
        {
            'UserID': member[0],
            'Username': member[1],
            'ProfilePic': member[2] if member[2] else 'https://example.com/default-profile-pic.jpg'  # ProfilePic이 NULL이면 기본 URL 사용
        }
        for member in team_members_tuples if member[0] != current_user.id
    ]

    # 현재 사용자의 프로필 사진을 가져옵니다.
    cursor.execute("SELECT ProfilePic FROM Users WHERE UserID = %s", (current_user.id,))
    current_user_pic_tuple = cursor.fetchone()
    current_user_pic = current_user_pic_tuple[0] if current_user_pic_tuple[0] else 'https://example.com/default-profile-pic.jpg'

    return render_template('team.html', name=current_user.username, current_page='team', team_members=team_members, current_user_pic=current_user_pic)

# 팀 편집 라우트
@app.route('/edit_team_member/<int:user_id>')
@login_required
def edit_team_member(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT UserID, Username, ProfilePic FROM Users WHERE UserID = %s", (user_id,))
    user_details_tuple = cursor.fetchone()
    cursor.close()

    if user_details_tuple:
        # Convert the tuple to a dictionary
        user_details = {
            'UserID': user_details_tuple[0],
            'Username': user_details_tuple[1],
            'ProfilePic': user_details_tuple[2]
        }
        # If user details are found, pass them to the template.
        return render_template('team_edit.html', name=current_user.username, user=user_details)
    else:
        # If no details are found, redirect to the team page with an error message.
        flash('No user found with that ID.', 'danger')
        return redirect(url_for('team'))

# 팀 실질적 편집 라우트
@app.route('/process_edit_team_member/<int:user_id>', methods=['POST'])
@login_required
def process_edit_team_member(user_id):
    new_username = request.form.get('username')
    # Add additional fields as necessary, and don't forget to validate the inputs

    # Update the database with the new details
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE Users SET Username = %s WHERE UserID = %s", (new_username, user_id))
    mysql.connection.commit()
    cursor.close()

    # flash('Team member updated successfully!', 'success')
    return redirect(url_for('team'))

# 팀 추가 라우트
@app.route('/add_team_member')
@login_required
def team_add():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT UserID, Username FROM Users WHERE TeamID IS NULL")
    users = cursor.fetchall()
    cursor.close()
    print(users)
    return render_template('team_add.html', name=current_user.username, users=users)


# 팀 실질적 추가 라우트
@app.route('/process_add_team_member', methods=['POST'])
@login_required
def process_add_team_member():
    user_id = request.form.get('user_id')
    if user_id:
        cursor = mysql.connection.cursor()
        # 팀 ID 설정을 원하는 값으로 업데이트하세요.
        cursor.execute("UPDATE Users SET TeamID = %s WHERE UserID = %s", ([1], user_id))
        mysql.connection.commit()
        cursor.close()
        # flash('Team member added successfully!', 'success')
    else:
        flash('No user selected.', 'danger')
    return redirect(url_for('team'))


# 팀 삭제 라우트
@app.route('/delete_team_member/<int:user_id>', methods=['POST'])
@login_required
def delete_team_member(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE Users SET TeamID = NULL WHERE UserID = %s", (user_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Team member removed successfully!', 'success')
    return redirect(url_for('team'))

# 채팅 -----------------------------------------------------------------------

# 채팅 라우트
@app.route('/chat')
def chat():
    return render_template('chat.html', current_page='chat')


if __name__ == '__main__':
    app.run(debug=True)
