import asyncio
import logs
import json
import httpx

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

async def create_response(request):
    # Извлекаем метод, путь и версию HTTP из запроса
    request_line, *headers, _ = request.split('\r\n')
    method, path, version = request_line.split()

    # Формируем URL для перенаправления
    url = f"http://{path}"

    # Формируем заголовки для перенаправления
    headers_dict = {}
    for header in headers:
        if header:
            key, value = header.split(': ', 1)
            headers_dict[key] = value

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

            response_to_client = await create_response(client_request)
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
        print("сервер запущен навсегда")
        await server.serve_forever()  # запускаем сервер до явного закрытия

if __name__ == "__main__":
    asyncio.run(start_server())
