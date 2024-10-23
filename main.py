import http.server
import socketserver
import requests
from urllib.parse import urlparse

PORT = 8080

class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = self.path[1:]
        if not url.startswith('http'):
            url = 'http://' + url
        print(f"Proxying GET request to {url}")

        try:
            response = requests.get(url)
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
            url = 'http://' + url  # Добавляем схему если ее нет
        print(f"Proxying POST request to {url}")

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            response = requests.post(url, data=post_data, headers=self.headers)
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
