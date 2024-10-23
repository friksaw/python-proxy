import http.server
import socketserver
import requests

PORT = 8080

class Proxy(http.server.SimpleHTTPRequestHandler):
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

            # Handle chunked encoding
            if 'Transfer-Encoding' in response.headers and response.headers['Transfer-Encoding'] == 'chunked':
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:  # Check if chunk is not empty
                        chunk_length = int(chunk.splitlines()[0], 16)  # Read chunk length
                        self.wfile.write(chunk[len(chunk.splitlines()[0]) + 2:]) # Skip length and newline
            else:
                # Regular content (not chunked)
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

        # Обновим заголовки и удалим неявные заголовки
        headers = {key: self.headers[key] for key in self.headers if key.lower() != 'host'}

        try:
            response = requests.post(url, data=post_data, headers=headers, allow_redirects=True, stream=True)
            self.send_response(response.status_code)
            for header, value in response.headers.items():
                self.send_header(header, value)
            self.end_headers()

            # Handle chunked encoding
            if 'Transfer-Encoding' in response.headers and response.headers['Transfer-Encoding'] == 'chunked':
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        chunk_length = int(chunk.splitlines()[0], 16)
                        self.wfile.write(chunk[len(chunk.splitlines()[0]) + 2:])
            else:
                # Regular content (not chunked)
                self.wfile.write(response.content)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

with socketserver.TCPServer(("", PORT), Proxy) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
