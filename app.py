import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.secret_key = "super-secret-key-123"  # для сессий
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# === БАЗА СООБЩЕНИЙ ===
messages = []

# === ГЛАВНАЯ СТРАНИЦА (красивый чат) ===
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    is_admin = session.get('is_admin', False)
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 МегаЧат</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg: #0f0f23;
            --card: #1a1a2e;
            --accent: #00ff88;
            --text: #e0e0ff;
            --msg-user: #16213e;
            --msg-admin: #2d1b3a;
        }
        * { margin:0; padding:0; box-sizing:border-box; font-family: 'Segoe UI', sans-serif; }
        body {
            background: linear-gradient(135deg, var(--bg), #16213e);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            background: rgba(0,0,0,0.4);
            padding: 1rem;
            text-align: center;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--accent);
        }
        h1 { font-size: 2rem; color: var(--accent); text-shadow: 0 0 10px var(--accent); }
        .container {
            flex: 1;
            max-width: 900px;
            margin: 2rem auto;
            padding: 0 1rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        #chat {
            background: var(--card);
            height: 65vh;
            overflow-y: auto;
            padding: 1.5rem;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,255,136,0.2);
            border: 1px solid rgba(0,255,136,0.3);
        }
        .msg {
            margin: 0.8rem 0;
            padding: 0.9rem 1.2rem;
            border-radius: 18px;
            max-width: 80%;
            word-wrap: break-word;
            animation: fadeIn 0.4s;
            position: relative;
        }
        .user { align-self: flex-end; background: var(--msg-user); color: #a0d8ff; }
        .admin { align-self: flex-start; background: var(--msg-admin); color: #ff99cc; border: 1px solid var(--accent); }
        .admin::before { content: "👑 "; }
        .input-area {
            display: flex;
            gap: 0.5rem;
            background: var(--card);
            padding: 1rem;
            border-radius: 50px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        }
        #msg {
            flex: 1;
            padding: 1rem 1.5rem;
            border: none;
            border-radius: 25px;
            background: #16213e;
            color: white;
            font-size: 1rem;
            outline: none;
        }
        button {
            padding: 0 1.5rem;
            background: var(--accent);
            color: black;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: 0.3s;
        }
        button:hover { transform: scale(1.05); box-shadow: 0 0 15px var(--accent); }
        .logout {
            position: fixed;
            top: 1rem;
            right: 1rem;
            background: #ff3366;
            padding: 0.7rem 1rem;
            border-radius: 30px;
            color: white;
            text-decoration: none;
            font-size: 0.9rem;
        }
        @keyframes fadeIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; } }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 4px; }
    </style>
</head>
<body>
    <header>
        <h1><i class="fas fa-comments"></i> МегаЧат</h1>
    </header>
    <a href="/logout" class="logout"><i class="fas fa-sign-out-alt"></i> Выйти</a>
    
    <div class="container">
        <div id="chat"></div>
        
        <div class="input-area">
            <input type="text" id="msg" placeholder="Напиши что-нибудь крутое..." autocomplete="off">
            <button onclick="send()">Отправить</button>
        </div>
    </div>

    <script>
        const socket = io();
        const chat = document.getElementById('chat');
        const input = document.getElementById('msg');
        
        socket.on('new_message', data => {
            const div = document.createElement('div');
            div.className = 'msg ' + (data.is_admin ? 'admin' : 'user');
            div.innerHTML = data.text;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        });
        
        function send() {
            const text = input.value.trim();
            if (!text) return;
            socket.emit('send_message', { text, is_admin: {{ 'true' if is_admin else 'false' }} });
            input.value = '';
        }
        
        input.addEventListener('keypress', e => { if (e.key === 'Enter') send(); });
        
        // Загрузка старых сообщений
        fetch('/history').then(r => r.json()).then(msgs => {
            msgs.forEach(m => {
                const div = document.createElement('div');
                div.className = 'msg ' + (m.is_admin ? 'admin' : 'user');
                div.innerHTML = m.text;
                chat.appendChild(div);
            });
            chat.scrollTop = chat.scrollHeight;
        });
    </script>
</body>
</html>
    ''', is_admin=is_admin)

# === СТРАНИЦА ЛОГИНА ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        if login == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['is_admin'] = True
            return redirect('/')
        elif login and password:  # любой логин/пароль = обычный юзер
            session['logged_in'] = True
            session['is_admin'] = False
            return redirect('/')
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход в МегаЧат</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600&display=swap');
        body {
            margin:0; height:100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display:flex; align-items:center; justify-content:center; font-family:'Poppins',sans-serif;
        }
        .card {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(15px);
            padding: 3rem 2.5rem;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            width: 350px;
            text-align:center;
            border: 1px solid rgba(255,255,255,0.2);
        }
        h2 { color: white; margin-bottom: 2rem; font-size: 2rem; }
        input {
            width: 100%; padding: 1rem; margin: 0.8rem 0;
            border: none; border-radius: 10px;
            background: rgba(255,255,255,0.2);
            color: white; font-size: 1rem;
            outline: none;
        }
        input::placeholder { color: #ddd; }
        button {
            width: 100%; padding: 1rem; margin-top: 1rem;
            background: #00ff88; color: black; border: none;
            border-radius: 10px; cursor:pointer; font-weight:bold;
            transition: 0.3s;
        }
        button:hover { background: #00cc66; transform: translateY(-3px); }
        .hint { color: #ff99cc; font-size: 0.8rem; margin-top: 1rem; }
    </style>
</head>
<body>
    <div class="card">
        <h2><i class="fas fa-shield-alt"></i> Вход</h2>
        <form method="post">
            <input name="login" placeholder="Логин" required>
            <input name="password" type="password" placeholder="Пароль" required>
            <button type="submit">Войти</button>
        </form>
        <div class="hint">
            👑 admin / admin — админка<br>
            любой логин+пароль — обычный чат
        </div>
    </div>
</body>
</html>
    ''')

# === ВЫХОД ===
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# === ИСТОРИЯ СООБЩЕНИЙ ===
@app.route('/history')
def history():
    return {"messages": messages}

# === SOCKET ===
@socketio.on('send_message')
def handle_message(data):
    text = data['text']
    is_admin = data.get('is_admin', False)
    
    msg_html = f"<b>{'Админ' if is_admin else 'Юзер'}:</b> {text}"
    messages.append({"text": msg_html, "is_admin": is_admin})
    
    emit('new_message', {"text": msg_html, "is_admin": is_admin}, broadcast=True)

# === ЗАПУСК ===
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
