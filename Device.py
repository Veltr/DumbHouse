import socket

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

        data = self._sock.recv(1024)
        mac = int.from_bytes(data[:8], 'big')
        print(mac)



    def execute(self):
        if self._sock is None:
            self.first_connection()
            return

        while True:
            a = 0

if __name__ == "__main__":
    d = Device(10, ("localhost", 9999))
    d.execute()
