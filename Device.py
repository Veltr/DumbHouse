import random
import socket
from diffiehellman import DiffieHellman as DH
from Cryptodome.Cipher import DES, AES

import time

class Device:
    mac = 0

    _master = ("", 0)
    _key = b''
    _sock = None

    _aes = None
    _aes_decr = None

    # ВРЕМЕННЫЙ КОНСТРУКТОР
    def __init__(self, mac, master, key=b''):
        self.mac = mac
        self._master = master
        self._key = key

    # def __init__(self, mac):
    #     self.mac = mac
    #     self.get_all()

    def get_all(self):
        pass

    def first_connection(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(self._master)

        self._sock.sendall(b'\x01' + self.mac.to_bytes(8, 'big'))

        t = self._sock.recv(1)
        if t == b'\x01':
            self.key_exchange()
        elif t == b'\x02':
            self.aes_nonce_exchange()
        elif t == b'\x00':
            self._sock.detach()
            self._sock = None
            return

        self.send_status()

    def key_exchange(self):
        dh = DH(group=14, key_bits=128)
        dh_public = dh.get_public_key()
        self._sock.sendall(dh_public)

        self._key = dh.generate_shared_key(self._sock.recv(256))[:32]
        self.aes_nonce_exchange()

    def aes_nonce_exchange(self):
        self._aes = AES.new(self._key, AES.MODE_EAX)
        des = DES.new(self._key[:8], DES.MODE_ECB)
        self._sock.sendall(des.encrypt(self._aes.nonce))
        self._aes_decr = AES.new(self._key, AES.MODE_EAX, nonce=des.decrypt(self._sock.recv(16)))

        # self._sock.sendall(self.encrypt(b'abacaba'))

    def encrypt(self, msg):
        return self._aes.encrypt(msg)

    def decrypt(self, msg):
        return self._aes_decr.decrypt(msg)

    def send_status(self):
        self._sock.sendall(b'\x00')


    def execute(self):
        if self._aes is None:
            self.first_connection()
            # return

        while True:
            self.send_status()
            time.sleep(3)


# Данные, лежащие в условном EPROM'е:
# mac
# зарегестрирован ли где-то, если да, адрес мастера, datetime окончания регистрации
# ключ, если есть

# Устройство может быть зарегестрировано только на одного мастера
# Если мастер уже имеется, необходимо перед новым подключением удалить старое

if __name__ == "__main__":
    # mac = 10
    mac = random.randint(1, 999999)
    d = Device(mac, ("localhost", 9999))
    d.execute()
