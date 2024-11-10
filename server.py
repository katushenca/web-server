import asyncio
import logs
import json
import httpx

with open('config.json', 'r') as config_file:
    config = json.load(config_file)


def create_response(request):
    path = request.split()[1]
    html_content = ''
    status_code = 200

    try:
        if path == "/home" or path == "/lizka":
            html_content = read_html_file(f"html files/{path}.html")
        elif path == '/':
            html_content = read_html_file("html files/hello.html")
        elif path == '/katya':
            html_content = read_html_file("html files/katya.html")

        if html_content:
            response = f"HTTP/1.1 {status_code} OK\r\nContent-Type: text/html\r\n\r\n{html_content}"
            return status_code, response

        if path.startswith("/redirect"):
            status_code = 301
            print(status_code)
            redirect_content = read_html_file("html files/3xx.html")
            response = f"HTTP/1.1 {status_code} Moved Permanently\r\nLocation: /home\r\nContent-Type: text/html\r\n\r\n{redirect_content if redirect_content else '<h1>301 Moved Permanently</h1>'}"
            return status_code, response

        elif path.startswith("/forbidden"):
            status_code = 403
            forbidden_content = read_html_file("html files/403.html")
            response = f"HTTP/1.1 {status_code} Forbidden\r\nContent-Type: text/html\r\n\r\n{forbidden_content}"
            return status_code, response

        elif path.startswith("/server_error"):

            raise ValueError("Intentional Server Error for testing")

        status_code = 404
        not_found_content = read_html_file("html files/4xx.html")
        response = f"HTTP/1.1 {status_code} Not Found\r\nContent-Type: text/html\r\n\r\n{not_found_content}"
        return status_code, response

    except Exception as e:
        status_code = 500
        server_error_content = read_html_file("html files/5xx.html")
        response = f"HTTP/1.1 {status_code} Internal Server Error\r\nContent-Type: text/html\r\n\r\n{server_error_content if server_error_content else f'<h1>500 Internal Server Error: {e}</h1>'}"
        return status_code, response

    # Отправляем запрос к целевому серверу
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers_dict)

    # Формируем ответ для клиента
    response_headers = '\r\n'.join(f"{key}: {value}" for key, value in response.headers.items())
    response_body = response.text

    return f"HTTP/1.1 {response.status_code} {response.reason}\r\n{response_headers}\r\n\r\n{response_body}"

async def work_with_client(reader, writer):
    client_address = writer.get_extra_info('peername')[0]
    while True:
        try:
            client_request = (await reader.read(1024)).decode()
            if not client_request:
                break

            print(f"Received: {client_request}")
            status_code, response_to_client = create_response(client_request)
            http_status = f"{status_code} {response_to_client.split()[1]}"
            logs.log_http_request(client_request, client_address, http_status)
            if 500 <= status_code < 600:
                print(f"Server error occurred with status {status_code}")

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
        await server.serve_forever()



if __name__ == "__main__":
    asyncio.run(start_server())
