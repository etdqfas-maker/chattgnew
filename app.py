import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.secret_key = "super-secret-key-123"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

messages = []

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if session.get('is_admin', False):
        return redirect(url_for('admin'))
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Чат</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: system-ui, sans-serif; background: #fff; color: #000; margin: 0; display: flex; flex-direction: column; height: 100vh; }
        #chat { flex: 1; overflow-y: auto; padding: 1rem; border-bottom: 1px solid #eee; }
        .msg { margin-bottom: 0.5rem; }
        .admin-msg { font-weight: bold; }
        .input-area { display: flex; padding: 1rem; }
        #msg { flex: 1; border: 1px solid #eee; padding: 0.5rem; margin-right: 0.5rem; outline: none; }
        button { background: #eee; border: none; padding: 0.5rem 1rem; cursor: pointer; }
        .logout { position: absolute; top: 1rem; right: 1rem; text-decoration: none; color: #000; }
        @media (max-width: 600px) { body { font-size: 16px; } .input-area { padding: 0.5rem; } }
    </style>
</head>
<body>
    <a href="/logout" class="logout">Выйти</a>
    <div id="chat"></div>
    <div class="input-area">
        <input type="text" id="msg" placeholder="Сообщение...">
        <button onclick="send()">Отправить</button>
    </div>
    <script>
        const socket = io();
        const chat = document.getElementById('chat');
        const input = document.getElementById('msg');
        
        socket.on('new_message', data => {
            const div = document.createElement('div');
            div.className = 'msg' + (data.is_admin ? ' admin-msg' : '');
            div.textContent = data.text;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        });
        
        function send() {
            const text = input.value.trim();
            if (!text) return;
            socket.emit('send_message', { text, is_admin: false });
            input.value = '';
        }
        
        input.addEventListener('keypress', e => { if (e.key === 'Enter') send(); });
        
        fetch('/history').then(r => r.json()).then(msgs => {
            msgs.forEach(m => {
                const div = document.createElement('div');
                div.className = 'msg' + (m.is_admin ? ' admin-msg' : '');
                div.textContent = m.text;
                chat.appendChild(div);
            });
            chat.scrollTop = chat.scrollHeight;
        });
    </script>
</body>
</html>
    ''')

@app.route('/admin')
def admin():
    if not session.get('is_admin', False):
        return "Доступ запрещен", 403
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админ</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: system-ui, sans-serif; background: #fff; color: #000; margin: 0; display: flex; flex-direction: column; height: 100vh; }
        #chat { flex: 1; overflow-y: auto; padding: 1rem; border-bottom: 1px solid #eee; }
        .msg { margin-bottom: 0.5rem; }
        .admin-msg { font-weight: bold; }
        .input-area { display: flex; padding: 1rem; }
        #msg { flex: 1; border: 1px solid #eee; padding: 0.5rem; margin-right: 0.5rem; outline: none; }
        button { background: #eee; border: none; padding: 0.5rem 1rem; cursor: pointer; }
        .logout { position: absolute; top: 1rem; right: 1rem; text-decoration: none; color: #000; }
        @media (max-width: 600px) { body { font-size: 16px; } .input-area { padding: 0.5rem; } }
    </style>
</head>
<body>
    <a href="/logout" class="logout">Выйти</a>
    <div id="chat"></div>
    <div class="input-area">
        <input type="text" id="msg" placeholder="Сообщение от админа...">
        <button onclick="send()">Отправить</button>
    </div>
    <script>
        const socket = io();
        const chat = document.getElementById('chat');
        const input = document.getElementById('msg');
        
        socket.on('new_message', data => {
            const div = document.createElement('div');
            div.className = 'msg' + (data.is_admin ? ' admin-msg' : '');
            div.textContent = data.text;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        });
        
        function send() {
            const text = input.value.trim();
            if (!text) return;
            socket.emit('send_message', { text, is_admin: true });
            input.value = '';
        }
        
        input.addEventListener('keypress', e => { if (e.key === 'Enter') send(); });
        
        fetch('/history').then(r => r.json()).then(msgs => {
            msgs.forEach(m => {
                const div = document.createElement('div');
                div.className = 'msg' + (m.is_admin ? ' admin-msg' : '');
                div.textContent = m.text;
                chat.appendChild(div);
            });
            chat.scrollTop = chat.scrollHeight;
        });
    </script>
</body>
</html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_val = request.form.get('login')
        password = request.form.get('password')
        
        if login_val == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['is_admin'] = True
            return redirect(url_for('admin'))
        
        elif login_val and password:
            session['logged_in'] = True
            session['is_admin'] = False
            return redirect(url_for('index'))
        
        return "Ошибка", 401
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #fff; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        form { width: 100%; max-width: 300px; padding: 1rem; }
        input { width: 100%; margin-bottom: 0.5rem; padding: 0.5rem; border: 1px solid #eee; outline: none; }
        button { width: 100%; background: #eee; border: none; padding: 0.5rem; cursor: pointer; }
        @media (max-width: 600px) { form { padding: 0.5rem; } }
    </style>
</head>
<body>
    <form method="post">
        <input name="login" placeholder="Логин" required>
        <input name="password" type="password" placeholder="Пароль" required>
        <button type="submit">Войти</button>
    </form>
</body>
</html>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/history')
def history():
    return {"messages": messages}

@socketio.on('send_message')
def handle_message(data):
    text = data['text']
    is_admin = data.get('is_admin', False)
    msg_text = f"{'Админ: ' if is_admin else ''}{text}"
    messages.append({"text": msg_text, "is_admin": is_admin})
    emit('new_message', {"text": msg_text, "is_admin": is_admin}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
