import asyncio
import logs
import json
import os


with open('config.json', 'r') as config_file:
    config = json.load(config_file)

def create_response(request):
    path = request.split()[1]
    html_content = ''
    if path == "/home" or path == "/lizka" :
        html_content = read_html_file(f"html files/{path}.html")
    elif path == '/':
        html_content = read_html_file("html files/hello.html")


    if html_content:
        return f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" \
               f"   {html_content}"
    else:
        return f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n" \
               f"\r\n<h1>404 Not Found</h1>"


def read_html_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None


async def work_with_client(reader, writer):
    client_address = writer.get_extra_info('peername')[0]
    while True:
        try:
            client_request = (await reader.read(100)).decode()
            if not client_request:
                break

            print(f"Received: {client_request}")

            response_to_client = create_response(client_request)
            http_status = " ".join(response_to_client.split()[1:3])
            print(http_status)
            logs.log_http_request(client_request, client_address, http_status)
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
