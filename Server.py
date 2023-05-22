import http.server
import socket
import socketserver
import threading
import time
from http import HTTPStatus

from diffiehellman import DiffieHellman as DH
from Cryptodome.Cipher import DES, AES
import sqlite3 as sql

# type - 1 B
#   0x00 - normal checkout
#   0x01 - first connection
#       mac - 8 B
#   0x02 - status


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
    _mac = 0
    _key = b''
    _aes = None
    _aes_decr = None
    def __del__(self):
        print('I m gone')

    def key_exchange(self):
        dh = DH(group=14, key_bits=128)
        dh_public = dh.get_public_key()
        self._key = dh.generate_shared_key(self.request.recv(256))[:32]
        self.request.sendall(dh_public)
        self.aes_nonce_exchange()

    def aes_nonce_exchange(self):
        self._aes = AES.new(self._key, AES.MODE_EAX)
        des = DES.new(self._key[:8], DES.MODE_ECB)
        self._aes_decr = AES.new(self._key, AES.MODE_EAX, nonce=des.decrypt(self.request.recv(16)))
        self.request.sendall(des.encrypt(self._aes.nonce))

        # print(self.decrypt(self.request.recv(1024)))

    def encrypt(self, msg):
        return self._aes.encrypt(msg)

    def decrypt(self, msg):
        return self._aes_decr.decrypt(msg)

    def handle_first_connection(self):
        self._mac = int.from_bytes(self.request.recv(8), 'big')
        device = find_device(self._mac)

        # 0 - Разрыв соединения, 1 - Подтверждение обмена, 2 - Используем старый ключ
        if not device:
            self.request.sendall(b'\x01')
            self.key_exchange()
            add_device(self._mac, self._key)
        else:
            self.request.sendall(b'\x02')
            self._key = device[1]
            self.aes_nonce_exchange()

    def handle(self):
        while True:
            ty = self.request.recv(1)
            if not ty:
                time.sleep(.5)
                continue

            ty = ty[0]
            if ty > 0x10:
                data = b""
                data += ty.to_bytes(1, 'big')
                while True:
                    b = self.request.recv(1)
                    data += b
                    if b == b'\n':
                        break

                HTTPHandler(self.request, self.client_address, self.server, data)
                return

            elif ty == 0x01:
                self.handle_first_connection()
            elif ty == 0x00:
                print('Zero ' + str(self.client_address))



class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def service_actions(self):
        # print('Hello there')
        pass


def find_device(mac):
    return db.execute('SELECT * FROM Device where mac == ?', (mac,)).fetchone()


def add_device(mac, key):
    db.execute('INSERT INTO Device (mac, s_key) values(?, ?)', (mac, key))
    db.commit()


def init_db():
    con = sql.connect(db_path, check_same_thread=False)
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
    with ThreadedTCPServer((HOST, PORT), TCPHandler) as server:
        server_thread = threading.Thread(target=server.serve_forever, args=[.5])
        server_thread.daemon = True
        server_thread.start()
        server_thread.join()

