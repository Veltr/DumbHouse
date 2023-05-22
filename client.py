import socket

HOST, PORT = "localhost", 9999

data = 1 << 4 | 1

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))
    sock.sendall(bytes(data))

    received = str(sock.recv(1024), "utf-8")

print(f"Отправлено: {data}")
print(f"Получено: {received}")