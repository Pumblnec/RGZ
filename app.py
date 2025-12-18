from flask import Flask, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Хранение данных в памяти
users = []
tickets = []
user_id_counter = 1
ticket_id_counter = 1

class User(UserMixin):
    def __init__(self, id, username, password, role='user'):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

# Создаем первого админа при запуске
users.append(User(
    id=user_id_counter,
    username='superadmin',
    password=generate_password_hash('admin123'),
    role='admin'
))
user_id_counter += 1

@login_manager.user_loader
def load_user(user_id):
    for user in users:
        if str(user.id) == str(user_id):
            return user
    return None

# Регистрация
@app.route('/register', methods=['POST'])
def register():
    global user_id_counter
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Всегда 'user', игнорируем роль из запроса
    role = 'user'

    for user in users:
        if user.username == username:
            return jsonify({'error': 'User already exists'}), 400

    new_user = User(
        id=user_id_counter,
        username=username,
        password=generate_password_hash(password),
        role=role
    )
    users.append(new_user)
    user_id_counter += 1
    return jsonify({'message': 'User created', 'role': role}), 201

# Вход
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    for user in users:
        if user.username == data['username'] and check_password_hash(user.password, data['password']):
            login_user(user)
            return jsonify({'message': 'Logged in', 'role': user.role})
    return jsonify({'error': 'Invalid credentials'}), 401

# Выход
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'})

# Создание тикета
@app.route('/tickets', methods=['POST'])
@login_required
def create_ticket():
    global ticket_id_counter
    data = request.json
    new_ticket = {
        'id': ticket_id_counter,
        'title': data['title'],
        'description': data['description'],
        'user_id': current_user.id,
        'status': 'open'
    }
    tickets.append(new_ticket)
    ticket_id_counter += 1
    return jsonify({'message': 'Ticket created', 'id': new_ticket['id']}), 201

# Получить все тикеты
@app.route('/tickets', methods=['GET'])
@login_required
def get_tickets():
    if current_user.role == 'admin':
        return jsonify(tickets)
    else:
        user_tickets = [t for t in tickets if t['user_id'] == current_user.id]
        return jsonify(user_tickets)

# Получить один тикет
@app.route('/tickets/<int:ticket_id>', methods=['GET'])
@login_required
def get_ticket(ticket_id):
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            if current_user.role == 'admin' or ticket['user_id'] == current_user.id:
                return jsonify(ticket)
    return jsonify({'error': 'Ticket not found or access denied'}), 404

# Обновить тикет
@app.route('/tickets/<int:ticket_id>', methods=['PUT'])
@login_required
def update_ticket(ticket_id):
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            if current_user.role != 'admin' and ticket['user_id'] != current_user.id:
                return jsonify({'error': 'Access denied'}), 403
            data = request.json
            ticket['title'] = data.get('title', ticket['title'])
            ticket['description'] = data.get('description', ticket['description'])
            ticket['status'] = data.get('status', ticket['status'])
            return jsonify({'message': 'Ticket updated'})
    return jsonify({'error': 'Ticket not found'}), 404

# Удалить тикет
@app.route('/tickets/<int:ticket_id>', methods=['DELETE'])
@login_required
def delete_ticket(ticket_id):
    global tickets
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            if current_user.role != 'admin' and ticket['user_id'] != current_user.id:
                return jsonify({'error': 'Access denied'}), 403
            tickets = [t for t in tickets if t['id'] != ticket_id]
            return jsonify({'message': 'Ticket deleted'})
    return jsonify({'error': 'Ticket not found'}), 404

# Получить всех пользователей (только админ)
@app.route('/users', methods=['GET'])
@login_required
def get_users():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    result = [{'id': u.id, 'username': u.username, 'role': u.role} for u in users]
    return jsonify(result)

# Изменить роль пользователя (только админ)
@app.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    for user in users:
        if user.id == user_id:
            data = request.json
            user.role = data.get('role', user.role)
            return jsonify({'message': 'User role updated'})
    return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)