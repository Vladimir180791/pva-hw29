import http.client
import json
import socket
import threading
import time
from urllib.parse import urlparse

# Путь к модулю с сервером (может потребоваться изменение)
import sys
sys.path.insert(0, 'src')

from echo_server import run_server

def test_echo_server():
    """Основной тест echo сервера"""
    
    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server, kwargs={'host': '127.0.0.1', 'port': 8888})
    server_thread.daemon = True
    server_thread.start()
    
    # Даем серверу время на запуск
    time.sleep(0.1)
    
    try:
        # Тест 1: Базовый запрос без параметров
        conn = http.client.HTTPConnection("127.0.0.1", 8888)
        conn.request("GET", "/")
        response = conn.getresponse()
        
        assert response.status == 200
        data = response.read().decode('utf-8')
        assert "Request Method: GET" in data
        assert "Response Status: 200 OK" in data
        assert "Request Source:" in data
        conn.close()
        
        # Тест 2: Запрос с кастомным статусом
        conn = http.client.HTTPConnection("127.0.0.1", 8888)
        conn.request("GET", "/?status=404")
        response = conn.getresponse()
        
        assert response.status == 404
        data = response.read().decode('utf-8')
        assert "Response Status: 404 Not Found" in data
        conn.close()
        
        # Тест 3: Запрос с заголовками
        conn = http.client.HTTPConnection("127.0.0.1", 8888)
        headers = {"X-Custom-Header": "test-value", "User-Agent": "test-agent"}
        conn.request("GET", "/", headers=headers)
        response = conn.getresponse()
        
        assert response.status == 200
        data = response.read().decode('utf-8')
        assert "X-Custom-Header: test-value" in data
        assert "User-Agent: test-agent" in data
        conn.close()
        
        # Тест 4: Невалидный статус (должен вернуть 200)
        conn = http.client.HTTPConnection("127.0.0.1", 8888)
        conn.request("GET", "/?status=invalid")
        response = conn.getresponse()
        
        assert response.status == 200
        data = response.read().decode('utf-8')
        assert "Response Status: 200 OK" in data
        conn.close()
        
        # Тест 5: POST запрос
        conn = http.client.HTTPConnection("127.0.0.1", 8888)
        conn.request("POST", "/")
        response = conn.getresponse()
        
        assert response.status == 200
        data = response.read().decode('utf-8')
        assert "Request Method: POST" in data
        conn.close()
        
        # Тест 6: Статус 500
        conn = http.client.HTTPConnection("127.0.0.1", 8888)
        conn.request("GET", "/?status=500")
        response = conn.getresponse()
        
        assert response.status == 500
        data = response.read().decode('utf-8')
        assert "Response Status: 500 Internal Server Error" in data
        conn.close()
        
        # Тест 7: Мultiple requests (проверка, что сервер не падает)
        for i in range(3):
            conn = http.client.HTTPConnection("127.0.0.1", 8888)
            conn.request("GET", f"/?test={i}")
            response = conn.getresponse()
            assert response.status == 200
            conn.close()
        
        print("All tests passed!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise e

def test_echo_server_with_socket():
    """Тест с использованием raw socket для более низкоуровневой проверки"""
    
    # Создаем TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 8888))
    
    # Отправляем HTTP запрос
    request = (
        "GET /?status=418 HTTP/1.1\r\n"
        "Host: 127.0.0.1:8888\r\n"
        "X-Test-Header: test-value\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    client_socket.send(request.encode('utf-8'))
    
    # Получаем ответ
    response = b""
    while True:
        chunk = client_socket.recv(1024)
        if not chunk:
            break
        response += chunk
    
    response_str = response.decode('utf-8')
    
    # Проверяем статус
    assert "HTTP/1.1 418" in response_str
    assert "Response Status: 418 I'm a Teapot" in response_str
    assert "X-Test-Header: test-value" in response_str
    assert "Request Method: GET" in response_str
    
    client_socket.close()

def test_content_length():
    """Тест корректности заголовка Content-Length"""
    
    conn = http.client.HTTPConnection("127.0.0.1", 8888)
    conn.request("GET", "/")
    response = conn.getresponse()
    
    content_length = response.getheader('Content-Length')
    data = response.read()
    
    # Проверяем, что Content-Length соответствует фактической длине тела
    assert content_length is not None
    assert int(content_length) == len(data)
    
    conn.close()

if __name__ == "__main__":
    # Запускаем сервер для тестов
    import threading
    server_thread = threading.Thread(target=run_server, kwargs={'host': '127.0.0.1', 'port': 8888})
    server_thread.daemon = True
    server_thread.start()
    
    # Ждем немного для запуска сервера
    time.sleep(0.5)
    
    try:
        test_echo_server()
        test_echo_server_with_socket()
        test_content_length()
        print("✅ All tests completed successfully!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise e