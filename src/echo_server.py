import socket
import http.client # Для получения фраз статусов (например, 200 -> "OK")
from urllib.parse import urlparse, parse_qs

def run_server(host='127.0.0.1', port=5000):
    # Создаем сокет, использующий IPv4 (AF_INET) и TCP (SOCK_STREAM)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Решаем проблему "Address already in use"
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Привязываем сокет к адресу и порту
        server_socket.bind((host, port))
        # Начинаем прослушивать входящие подключения (макс. очередь = 5)
        server_socket.listen(5)
        print(f"Echo server is running on http://{host}:{port}")

        # Главный цикл сервера для многократного принятия соединений
        while True:
            # Принимаем новое соединение
            client_socket, client_address = server_socket.accept()
            print(f"Connection from: {client_address}")

            # Получаем данные от клиента (байты)
            request_data = client_socket.recv(1024).decode('utf-8')
            print(f"Received request:\n{request_data}")

            # Если запрос пустой, закрываем соединение и продолжаем ждать
            if not request_data:
                client_socket.close()
                continue

            # Парсим HTTP-запрос
            try:
                # Первая строка запроса (например, "GET /?status=404 HTTP/1.1")
                request_line = request_data.splitlines()[0]
                method, path, _ = request_line.split()
                
                # Парсим URL для получения query-параметров
                parsed_url = urlparse(path)
                query_params = parse_qs(parsed_url.query)
                
                # Извлекаем статус из параметра 'status', валидируем его
                status_code = 200 # Статус по умолчанию
                status_phrase = "OK"
                if 'status' in query_params:
                    try:
                        potential_code = int(query_params['status'][0])
                        # Проверяем, что это валидный HTTP-код статуса
                        if potential_code in http.client.responses:
                            status_code = potential_code
                            status_phrase = http.client.responses[potential_code]
                    except (ValueError, TypeError):
                        # Если параметр не число, используем статус 200
                        pass

            except Exception as e:
                # В случае любой ошибки парсинга возвращаем 400 Bad Request
                status_code = 400
                status_phrase = "Bad Request"
                method = "UNKNOWN"
                client_address = ("UNKNOWN", "UNKNOWN")
                # Формируем простой ответ об ошибке
                response_body = f"Error parsing request: {e}"
                response_headers = "Content-Type: text/plain; charset=utf-8\r\n"
                response = f"HTTP/1.1 {status_code} {status_phrase}\r\n{response_headers}\r\n{response_body}"
                client_socket.sendall(response.encode('utf-8'))
                client_socket.close()
                continue

            # Формируем тело ответа
            response_body_lines = [
                f"Request Method: {method}",
                f"Request Source: {client_address}",
                f"Response Status: {status_code} {status_phrase}",
            ]
            # Добавляем все заголовки запроса
            headers = request_data.splitlines()[1:] # Пропускаем первую строку (request line)
            for header in headers:
                if header.strip(): # Игнорируем пустые строки
                    response_body_lines.append(header)

            # Объединяем все строки тела ответа
            response_body = "\n".join(response_body_lines)

            # Формируем полный HTTP-ответ
            response_headers = [
                f"HTTP/1.1 {status_code} {status_phrase}",
                "Content-Type: text/plain; charset=utf-8",
                f"Content-Length: {len(response_body.encode('utf-8'))}",
                "Connection: close", # Закрываем соединение после ответа
                "", # Пустая строка, отделяющая заголовки от тела
            ]
            response = "\r\n".join(response_headers) + response_body

            # Отправляем ответ клиенту
            client_socket.sendall(response.encode('utf-8'))
            
            # Закрываем соединение с текущим клиентом
            client_socket.close()

if __name__ == '__main__':
    run_server()