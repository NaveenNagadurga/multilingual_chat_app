from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from deep_translator import GoogleTranslator
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")


@app.route('/')
def home():
    return render_template('login.html')


@app.route('/chat', methods=['GET'])
def chat_room():
    username = request.args.get('username', '').strip()
    language = request.args.get('language', '').strip()
    room = request.args.get('room', '').strip() or 'default'

    if not username or not language:
        return redirect(url_for('home'))

    session['username'] = username
    session['language'] = language
    session['room'] = room

    return render_template('chat.html', username=username, room=room)


@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    room = session.get('room')
    if username and room:
        join_room(room)
        emit('user_connected', {'username': username}, room=room)


@socketio.on('send_message')
def handle_send_message(data):
    username = session.get('username')
    user_language = session.get('language')
    room = session.get('room')

    message = (data or {}).get('message', '').strip()
    time = (data or {}).get('time', '')

    if not username or not message:
        return

    try:
        translated_message = GoogleTranslator(
            source='auto',
            target=user_language
        ).translate(message)
    except Exception:
        translated_message = message

    emit(
        'receive_message',
        {'username': username, 'message': translated_message, 'time': time},
        room=room
    )


@socketio.on('typing')
def handle_typing():
    """Broadcast typing status to others in the same room."""
    username = session.get('username')
    room = session.get('room')
    if username and room:
        emit('user_typing', {'username': username}, room=room, include_self=False)


@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    room = session.get('room')
    if username and room:
        emit('user_disconnected', {'username': username}, room=room)


if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=8000, debug=True)
