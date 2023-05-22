import socket
from diffiehellman import DiffieHellman as DH

class Device:
    mac = 0

    _master = ("", 0)
    _key = b""
    _sock = None

    def __init__(self, mac, master):
        self.mac = mac
        self._master = master

    def first_connection(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(self._master)

        out = self.mac.to_bytes(8, 'big') + (1).to_bytes(1, 'big')
        self._sock.sendall(out)

        t = self._sock.recv(1)
        if t == b'\x01':
            self.key_exchange()
        elif t == b'\x00':
            self._sock.detach()
            self._sock = None
            return


    def key_exchange(self):
        dh = DH(group=14, key_bits=128)
        dh_public = dh.get_public_key()
        self._sock.sendall(dh_public)

        self._key = dh.generate_shared_key(self._sock.recv(256))[:32]
        print(self._key)

    def execute(self):
        # if self._sock is None:
        if not self._key:
            self.first_connection()
            return

        while True:
            a = 0

if __name__ == "__main__":
    d = Device(10, ("localhost", 9999))
    d.execute()
