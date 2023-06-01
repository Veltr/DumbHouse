from datetime import datetime
import random
import socket
from diffiehellman import DiffieHellman as DH
from Cryptodome.Cipher import DES, AES

import time

class Device:
    class Master_Data:
        def __init__(self, address, key=b''):
            self.address = address
            self.key = key

        address = ("", 0)
        key = b''
        aes = None
        aes_decr = None

    mac = 0
    _sock = None

    _main_master: Master_Data = None
    _temp_master: Master_Data = None
    _temp_datetime: datetime = None

    _cur_master: Master_Data = None

    # ВРЕМЕННЫЙ КОНСТРУКТОР
    # def __init__(self, mac, master, key=b''):
    #     self.mac = mac
    #     self._main_master = Device.Master_Data(master, key)
    #     self._cur_master = self._main_master

    def __init__(self, mac, path):
        self.mac = mac
        file = open(path, 'r')
        s = file.readline().split(':')
        self._main_master = Device.Master_Data((s[0], int(s[1])))
        self._cur_master = self._main_master
        s = file.readline()
        if s != "":
            s = s.split(':')
            self._temp_master = Device.Master_Data((s[0], int(s[1])))
            self._temp_datetime = datetime.strptime(file.readline()[2:], '%y-%m-%d %H:%M:%S')
            self._cur_master = self._temp_master

    def first_connection(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(self._cur_master.address)

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

        self._cur_master.key = dh.generate_shared_key(self._sock.recv(256))[:32]
        self.aes_nonce_exchange()

    def aes_nonce_exchange(self):
        self._cur_master.aes = AES.new(self._cur_master.key, AES.MODE_EAX)
        des = DES.new(self._cur_master.key[:8], DES.MODE_ECB)
        self._sock.sendall(des.encrypt(self._cur_master.aes.nonce))
        self._cur_master.aes_decr = AES.new(self._cur_master.key, AES.MODE_EAX, nonce=des.decrypt(self._sock.recv(16)))

        self._sock.sendall(self.encrypt(b'abacaba'))

    def encrypt(self, msg):
        return self._cur_master.aes.encrypt(msg)

    def decrypt(self, msg):
        return self._cur_master.aes_decr.decrypt(msg)

    def send_status(self):
        self._sock.sendall(b'\x00')


    def execute(self):
        self.first_connection()

        while True:
            if not(self._temp_datetime is None) and datetime.now() > self._temp_datetime:
                print('Timeout')
                return

            t = self._sock.recv(1)
            print(t)
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
    # d = Device(mac, ("localhost", 9999))
    d = Device(mac, 'd_data.txt')
    d.execute()



