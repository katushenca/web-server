import socket

def read_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 5252))
server.listen(4)

while True:
    client, address = server.accept()
    data = client.recv(1024).decode("utf-8")
    print(data)
    path = data.split()[1]
    if path == "/home":
        html_content = read_html_file("html files/home.html")
    elif path == "/lizka":
        html_content = read_html_file("html files/lizka.html")
    else:
        html_content = read_html_file("html files/hello.html")
    response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html_content}"
    client.sendall(response.encode("utf-8"))
    client.close()