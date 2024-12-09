import http.server
import socket
import socketserver
import requests
import select

PORT = 16666

class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_CONNECT(self):
        host, port = self.path.split(':', 1)
        port = int(port)

        try:
            self.send_response(200, 'Connection Established')
            self.end_headers()
            tunnel_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tunnel_socket.connect((host, port))

            self.proxy_tunnel(tunnel_socket)

        except Exception as e:
            self.send_error(500, str(e))

    def proxy_tunnel(self, tunnel_socket):
        try:
            while True:
                rlist, _, _ = select.select([self.connection, tunnel_socket], [], [])
                for r in rlist:
                    if r is self.connection:
                        data = self.connection.recv(4096)
                        if not data:
                            return
                        tunnel_socket.sendall(data)
                    elif r is tunnel_socket:
                        data = tunnel_socket.recv(4096)
                        if not data:
                            return
                        self.connection.sendall(data)

        except Exception as e:
            print("Error in proxy tunnel:", e)
        finally:
            tunnel_socket.close()

    def do_GET(self):
        url = self.path[1:]  
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

        except requests.RequestException as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_POST(self):
        url = self.path[1:]  
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
        except requests.RequestException as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Proxy) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
