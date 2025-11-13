import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
messages = []
@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <title>Чат</title>
    <h2>Чат пользователя</h2>
    <div id="chat" style="height:300px;overflow-y:scroll;border:1px solid #ccc"></div>
    <input id="msg" placeholder="Введите сообщение..." style="width:70%"/>
    <button onclick="sendMessage()">Отправить</button>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    <script>
        var socket = io();
        socket.on('new_message', function(msg){
            var div = document.getElementById('chat');
            div.innerHTML += msg + '<br>';
            div.scrollTop = div.scrollHeight;
        });
        function sendMessage(){
            var input = document.getElementById('msg');
            if(input.value.trim() === "") return;
            socket.emit('send_message', input.value);
            input.value = '';
        }
    </script>
    ''')
@app.route('/admin')
def admin():
    return render_template_string('''
    <!doctype html>
    <title>Админ</title>
    <h2>Админ-панель</h2>
    <div id="chat" style="height:300px;overflow-y:scroll;border:1px solid #ccc"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    <script>
        var socket = io();
        socket.on('new_message', function(msg){
            var div = document.getElementById('chat');
            div.innerHTML += msg + '<br>';
            div.scrollTop = div.scrollHeight;
        });
    </script>
    ''')
@socketio.on('send_message')
def handle_message(msg):
    messages.append(msg)
    emit('new_message', msg, broadcast=True)
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)