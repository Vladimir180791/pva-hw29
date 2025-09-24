import socket
import http.client
from urllib.parse import urlparse, parse_qs

def run_server(host='127.0.0.1', port=5000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Echo server is running on http://{host}:{port}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection from: {client_address}")

            request_data = client_socket.recv(1024).decode('utf-8')
            print(f"Received request:\n{request_data}")

            if not request_data:
                client_socket.close()
                continue

            try:
                request_line = request_data.splitlines()[0]
                method, path, _ = request_line.split()
                
                parsed_url = urlparse(path)
                query_params = parse_qs(parsed_url.query)
                
                status_code = 200
                status_phrase = "OK"
                if 'status' in query_params:
                    try:
                        potential_code = int(query_params['status'][0])
                        if potential_code in http.client.responses:
                            status_code = potential_code
                            status_phrase = http.client.responses[potential_code]
                    except (ValueError, TypeError):
                        pass

            except Exception as e:
                status_code = 400
                status_phrase = "Bad Request"
                method = "UNKNOWN"
                client_address = ("UNKNOWN", "UNKNOWN")
                response_body = f"Error parsing request: {e}"
                
                # ИСПРАВЛЕННАЯ ЧАСТЬ: правильное разделение заголовков и тела
                response_headers = [
                    f"HTTP/1.1 {status_code} {status_phrase}",
                    "Content-Type: text/plain; charset=utf-8",
                    f"Content-Length: {len(response_body.encode('utf-8'))}",
                    "Connection: close",
                ]
                response = "\r\n".join(response_headers) + "\r\n\r\n" + response_body
                client_socket.sendall(response.encode('utf-8'))
                client_socket.close()
                continue

            # Формируем тело ответа
            response_body_lines = [
                f"Request Method: {method}",
                f"Request Source: {client_address}",
                f"Response Status: {status_code} {status_phrase}",
            ]
            
            headers = request_data.splitlines()[1:]
            for header in headers:
                if header.strip():
                    response_body_lines.append(header)

            response_body = "\n".join(response_body_lines)

            # ИСПРАВЛЕННАЯ ЧАСТЬ: правильное формирование HTTP ответа
            response_headers = [
                f"HTTP/1.1 {status_code} {status_phrase}",
                "Content-Type: text/plain; charset=utf-8",
                f"Content-Length: {len(response_body.encode('utf-8'))}",
                "Connection: close",
            ]
            
            # Собираем полный ответ: заголовки + пустая строка + тело
            response = "\r\n".join(response_headers) + "\r\n\r\n" + response_body

            # Отправляем ответ клиенту
            client_socket.sendall(response.encode('utf-8'))
            client_socket.close()

if __name__ == '__main__':
    run_server()