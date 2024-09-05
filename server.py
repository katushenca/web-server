import asyncio
import logs

def create_response(request):
    path = request.split()[1]
    if path == "/home" or path == "/lizka" :
        html_content = read_html_file(f"html files/{path}.html")
    else:
        html_content = read_html_file("html files/hello.html")
    return f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html_content}"


def read_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


async def work_with_client(reader, writer):
    client_request = (await reader.read(1024)).decode()
    logs.log_http_request(client_request)
    print(f"Received: {client_request}")

    response_to_client = create_response(client_request)
    writer.write(response_to_client.encode())

    print("Closing the connection")
    writer.close()
    await writer.wait_closed() #ждем пока до конца не закроем клиентика


async def start_server():
    server = await asyncio.start_server(work_with_client, '127.0.0.1', 5252)
    print("start server")
    async with server:
        print("cервер запущен навсегда")
        await server.serve_forever() # запускаем сервер до явного закрытия


if __name__ == "__main__":
    asyncio.run(start_server())
