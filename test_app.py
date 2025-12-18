import pytest
from app import app, users, tickets, user_id_counter, ticket_id_counter

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        with app.app_context():
            # Полный сброс данных
            users.clear()
            tickets.clear()
            global user_id_counter, ticket_id_counter
            user_id_counter = 1
            ticket_id_counter = 1
            yield client

def test_register(client):
    response = client.post('/register', json={
        'username': 'testuser',
        'password': '12345'
    })
    assert response.status_code == 201

def test_login(client):
    client.post('/register', json={'username': 'user1', 'password': '12345'})
    response = client.post('/login', json={'username': 'user1', 'password': '12345'})
    assert response.status_code == 200

def test_create_ticket(client):
    # Регистрация и вход
    client.post('/register', json={'username': 'user2', 'password': '12345'})
    response = client.post('/login', json={'username': 'user2', 'password': '12345'})
    assert response.status_code == 200
    
    # Создание тикета
    response = client.post('/tickets', json={
        'title': 'Test ticket',
        'description': 'Help me'
    })
    assert response.status_code == 201
    assert len(tickets) == 1

def test_user_sees_only_own_tickets(client):
    # Регистрация первого пользователя
    client.post('/register', json={'username': 'user3', 'password': '12345'})
    response = client.post('/login', json={'username': 'user3', 'password': '12345'})
    assert response.status_code == 200
    client.post('/tickets', json={'title': 'Ticket 1', 'description': 'test'})
    client.post('/logout')
    
    # Регистрация второго пользователя
    client.post('/register', json={'username': 'user4', 'password': '12345'})
    response = client.post('/login', json={'username': 'user4', 'password': '12345'})
    assert response.status_code == 200
    
    # Второй пользователь не видит тикет первого
    response = client.get('/tickets')
    assert response.status_code == 200
    assert len(response.json) == 0

def test_update_ticket(client):
    # Регистрация и вход
    client.post('/register', json={'username': 'user6', 'password': '12345'})
    response = client.post('/login', json={'username': 'user6', 'password': '12345'})
    assert response.status_code == 200
    
    # Создание тикета
    response = client.post('/tickets', json={'title': 'Old title', 'description': 'test'})
    ticket_id = response.json['id']  # Берем ID из ответа!
    
    # Обновление тикета
    response = client.put(f'/tickets/{ticket_id}', json={'title': 'New title'})
    assert response.status_code == 200
    
    # Проверяем, что обновилось
    response = client.get(f'/tickets/{ticket_id}')
    assert response.json['title'] == 'New title'

def test_delete_ticket(client):
    # Регистрация и вход
    client.post('/register', json={'username': 'user7', 'password': '12345'})
    response = client.post('/login', json={'username': 'user7', 'password': '12345'})
    assert response.status_code == 200
    
    # Создание тикета
    response = client.post('/tickets', json={'title': 'To delete', 'description': 'test'})
    ticket_id = response.json['id']  # Берем ID из ответа!
    
    # Удаление тикета
    response = client.delete(f'/tickets/{ticket_id}')
    assert response.status_code == 200
    
    # Проверяем, что удалился
    response = client.get(f'/tickets/{ticket_id}')
    assert response.status_code == 404