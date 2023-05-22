import http.server
import socket
import socketserver
from http import HTTPStatus


# mac - 8 B
# type - 1 B
#     0x01 - first connection
# key - 32 B


class HTTPHandler(http.server.SimpleHTTPRequestHandler):
    raw_requestline = b""
    def __init__(self, request: bytes, client_address: tuple[str, int], server: socketserver.BaseServer, data):
        self.raw_requestline = data
        print(self.raw_requestline)
        super().__init__(request, client_address, server)

    def handle_one_request(self):
        try:
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                return
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(
                    HTTPStatus.NOT_IMPLEMENTED,
                    "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            method()
            self.wfile.flush()
        except socket.timeout as e:
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        ttt = self.request.recv(1)

        if ttt != b'\0':
            data = b""
            data += ttt
            while True:
                b = self.request.recv(1)
                data += b
                if b == b'\n':
                    break

            print(data)
            HTTPHandler(self.request, self.client_address, self.server, data)
            return

        data = ttt + self.request.recv(1024)
        mac = int.from_bytes(data[:8], 'big')
        ty = data[8]

        if ty == 0x01:
            self.handle_first_connection(mac)
            return

    def handle_first_connection(self, mac):
        self.request.sendall(mac.to_bytes(8, 'big'))
        # pass



if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        server.serve_forever()