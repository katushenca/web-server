import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 5252))
server.listen(4)

while True:
    client, address = server.accept()
    data = client.recv(1024).decode("utf-8")
    print(data)
    path = data.split()[1]
    if path == "/home":
        response = \
            "HTTP/1.1 200 OK\r\n" \
            "Content-Type: text/html\r\n\r\n" \
            "<html><body><h1>home</h1></body></html>"
    else:
        response = \
            "HTTP/1.1 200 OK\r\n" \
            "Content-Type: text/html\r\n\r\n" \
            "<html><body><h1>hello</h1></body></html>"
    client.sendall(response.encode("utf-8"))
    client.close()