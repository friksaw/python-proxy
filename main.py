import http.server
import socket
import socketserver
import requests

PORT = 8080

class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_CONNECT(self):
        # Получаем адрес и порт целевого сервера из запроса
        host, port = self.path.split(':', 1)
        port = int(port)

        # Устанавливаем соединение с целевым сервером
        try:
            self.send_response(200, 'Connection Established')
            self.end_headers()

            # Создаем туннель
            self.connection.settimeout(5)
            # Можем использовать например socket.socket для туннелирования
            with requests.Session() as session:
                tunnel_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tunnel_socket.connect((host, port))

                # Обрабатываем данные, пришедшие с клиента
                while True:
                    data = self.connection.recv(4096)
                    if not data:
                        break
                    tunnel_socket.sendall(data)

                    # Ответ от сервера направляем обратно клиенту
                    response_data = tunnel_socket.recv(4096)
                    if not response_data:
                        break
                    self.connection.sendall(response_data)

        except Exception as e:
            self.send_error(500, str(e))

    def do_GET(self):
        url = self.path[1:]  # Убираем символ '/'
        if not url.startswith('http'):
            url = 'http://' + url
        print(f"Proxying GET request to {url}")

        try:
            response = requests.get(url, stream=True)
            self.send_response(response.status_code)
            for header, value in response.headers.items():
                self.send_header(header, value)
            self.end_headers()

            self.wfile.write(response.content)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_POST(self):
        url = self.path[1:]  # Убираем символ '/'
        if not url.startswith('http'):
            url = 'http://' + url
        print(f"Proxying POST request to {url}")

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        headers = {key: self.headers[key] for key in self.headers if key.lower() != 'host'}

        try:
            response = requests.post(url, data=post_data, headers=headers, allow_redirects=True, stream=True)
            self.send_response(response.status_code)
            for header, value in response.headers.items():
                self.send_header(header, value)
            self.end_headers()

            self.wfile.write(response.content)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

with socketserver.TCPServer(("", PORT), Proxy) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
