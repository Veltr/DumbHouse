import socket, sys

HOST, PORT = "localhost", 9999

data = "Help me "

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))
    sock.sendall(bytes(data + "\n", "utf-8"))

    received = str(sock.recv(1024), "utf-8")

print(f"Отправлено: {data}")
print(f"Получено: {received}")