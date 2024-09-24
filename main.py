from flask import Flask, render_template, request, jsonify
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
chat_history = []
online_users = set()
banned_users = set()

# Load banned users from a file
def load_banned_users():
    if os.path.exists('banned_users.json'):
        with open('banned_users.json', 'r') as f:
            return set(json.load(f))
    return set()

# Save banned users to a file
def save_banned_users():
    with open('banned_users.json', 'w') as f:
        json.dump(list(banned_users), f)

# Load banned users on startup
banned_users = load_banned_users()

# Ensure the uploads directory exists
if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

@app.route('/')
def chat():
    return render_template('chat.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    username = request.form['username']
    message = request.form['message']

    # Check if the user is banned
    if username in banned_users:
        return jsonify({'status': 'You are banned from this chat.'})

    # Handle image upload
    image_url = None
    if 'image' in request.files:
        image_file = request.files['image']
        if image_file:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join('static', 'uploads', filename)
            image_file.save(image_path)
            image_url = f'/static/uploads/{filename}'

    # Command handling for clear, ban, unban
    if message.startswith('/'):
        if message == '/clear':
            global chat_history
            chat_history = []  # Clear chat history
            send_system_message('The chat has been cleared.')
            return jsonify({'status': 'Chat cleared'})
        elif message.startswith('/ban '):
            user_to_ban = message.split(' ')[1].replace('_', ' ')
            banned_users.add(user_to_ban)
            save_banned_users()
            send_system_message(f'User {user_to_ban} has been banned.')
            return jsonify({'status': f'User {user_to_ban} has been banned.'})
        elif message.startswith('/unban '):
            user_to_unban = message.split(' ')[1].replace('_', ' ')
            if user_to_unban in banned_users:
                banned_users.remove(user_to_unban)
                save_banned_users()
                send_system_message(f'User {user_to_unban} has been unbanned.')
                return jsonify({'status': f'User {user_to_unban} has been unbanned.'})
            else:
                return jsonify({'status': f'User {user_to_unban} is not banned.'})

    # Add the message to chat history
    chat_history.append({'username': username, 'message': message, 'image': image_url})
    return jsonify({'status': 'Message sent'})

@app.route('/get_messages')
def get_messages():
    return jsonify(chat_history)

@app.route('/update_status', methods=['POST'])
def update_status():
    username = request.form['username']
    online = request.form['online'] == 'true'

    if online:
        online_users.add(username)
        send_system_message(f'Welcome {username} to the chat!')
    else:
        online_users.discard(username)

    return jsonify({'status': 'Status updated'})

@app.route('/get_online_users', methods=['GET'])
def get_online_users():
    return jsonify([{'username': user, 'online': True} for user in online_users])

def send_system_message(message):
    chat_history.append({'username': 'System', 'message': message, 'image': None})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
