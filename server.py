import asyncio
import logs
import json


with open('config.json', 'r') as config_file:
    config = json.load(config_file)

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
    while True:
        try:
            client_request = (await reader.read(1024)).decode()
            if not client_request:
                break
            logs.log_http_request(client_request)
            print(f"Received: {client_request}")

            response_to_client = create_response(client_request)
            writer.write(response_to_client.encode())
            await writer.drain()
            if config["keep-alive"]["using"] != "true":
                break
            else:
                if "Connection: keep-alive" in client_request:
                    print("Keeping the connection alive")
                    continue
                else:
                    print("Closing the connection")
                    break
        except asyncio.CancelledError:
            break

    writer.close()
    await writer.wait_closed()


async def start_server():
    server = await asyncio.start_server(
        work_with_client,
        config["server"]["host"],
        config["server"]["port"]
    )
    print("start server")
    async with server:
        print("cервер запущен навсегда")
        await server.serve_forever() # запускаем сервер до явного закрытия


if __name__ == "__main__":
    asyncio.run(start_server())
