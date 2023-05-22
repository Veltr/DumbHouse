import http.server
import socket
import socketserver
from http import HTTPStatus

from diffiehellman import DiffieHellman as DH
import sqlite3 as sql

# mac - 8 B
# type - 1 B
#     0x00 - normal checkout
#     0x01 - first connection
#     0x02 - status


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

class TCPHandler(socketserver.BaseRequestHandler):

    def key_exchange(self):
        dh = DH(group=14, key_bits=128)
        dh_public = dh.get_public_key()
        key = dh.generate_shared_key(self.request.recv(256))
        self.request.sendall(dh_public)

        return key[:32]

    def handle_first_connection(self, mac):
        device = find_device(mac)
        key = b''

        # 0 - Разрыв соединения, 1 - Подтверждение обмена, 2 - Используем старый ключ
        if device:
            self.request.sendall(b'\x02')
            key = device[1]
        else:
            self.request.sendall(b'\x01')
            key = self.key_exchange()
            add_device(mac, key)

        print(key)

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

        mac = int.from_bytes(self.request.recv(7), 'big')
        ty = self.request.recv(1)[0]

        if ty == 0x01:
            self.handle_first_connection(mac)
            return

def find_device(mac):
    return db.execute('SELECT * FROM Device where mac == ?', (mac,)).fetchone()


def add_device(mac, key):
    db.execute('INSERT INTO Device (mac, s_key) values(?, ?)', (mac, key))
    db.commit()


def init_db():
    con = sql.connect(db_path)
    con.execute('''
        CREATE TABLE IF NOT EXISTS Device (
            mac INT PRIMARY KEY,
            s_key BLOB
        );
    ''')
    con.commit()

    return con

db_path = r"resources/test.db"
db = init_db()

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    with socketserver.TCPServer((HOST, PORT), TCPHandler) as server:
        server.serve_forever()