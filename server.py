import asyncio
import logs
import json
import ssl
import os, datetime
import directory_indexation_auto

with open('config.json', 'r') as config_file:
    config = json.load(config_file)


def read_html_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None


# Define the paths that should trigger a redirect
REDIRECT_PATHS = ['/redirect1.html', '/redirect2.html']


def get_host(request):
    for line in request.split('\r\n'):
        if line.lower().startswith('host:'):
            return line.split(':', 1)[1].strip()
    return 'localhost'  # Default host if none is found


def create_response(request):
    path = request.split()[1]
    html_content = ''
    status_code = 200

    try:
        # Check if the requested path needs to be redirected
        if path in REDIRECT_PATHS:
            host = get_host(request)
            redirect_url = f"http://{host}:8081{path}"  # Используйте 'https://' если 8081 настроен на SSL
            response = (
                "HTTP/1.1 302 Found\r\n"
                f"Location: {redirect_url}\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 0\r\n"
                "\r\n"
            )
            return 302, response

        local_path = os.path.join(os.getcwd(), path).split('/')[1]
        print(local_path, 'fsdfsdfs')
        if os.path.isdir(local_path):
            html_content, status_code = directory_indexation_auto.generate_directory_index(
                local_path)
            response = f"HTTP/1.1 {status_code} OK\r\nContent-Type: text/html\r\n\r\n{html_content}"
            return status_code, response
        if os.path.isfile(local_path):
            file_name = os.path.basename(local_path)
            with open(local_path, 'rb') as file:
                file_data = file.read()

            response_headers = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/octet-stream\r\n"
                f"Content-Disposition: attachment; filename=\"{file_name}\"\r\n"
                f"Content-Length: {len(file_data)}\r\n"
                f"\r\n"
            )
            response = response_headers.encode('utf-8') + file_data
            return 200, response

        if path.startswith("/other"):
            html_content = read_html_file(f"html_files/other.html")
            response = f"HTTP/1.1 {status_code} OK\r\nContent-Type: text/html\r\n\r\n{html_content}"
            return status_code, response

        if path == "/home" or path == "/lizka":
            html_content = read_html_file(f"html_files/{path}.html")
        elif path == '/':
            html_content = read_html_file("html_files/hello.html")
        elif path == '/katya':
            html_content = read_html_file("html_files/katya.html")

        if html_content:
            response = f"HTTP/1.1 {status_code} OK\r\nContent-Type: text/html\r\n\r\n{html_content}"
            return status_code, response

        elif path.startswith("/forbidden"):
            status_code = 403
            forbidden_content = read_html_file("html_files/403.html")
            response = f"HTTP/1.1 {status_code} Forbidden\r\nContent-Type: text/html\r\n\r\n{forbidden_content}"
            return status_code, response

        elif path.startswith("/server_error"):
            raise ValueError("Intentional Server Error for testing")

        status_code = 404
        not_found_content = read_html_file("html_files/4xx.html")
        response = f"HTTP/1.1 {status_code} Not Found\r\nContent-Type: text/html\r\n\r\n{not_found_content}"
        return status_code, response

    except Exception as e:
        status_code = 500
        server_error_content = read_html_file("html_files/5xx.html")
        response = (
            f"HTTP/1.1 {status_code} Internal Server Error\r\n"
            "Content-Type: text/html\r\n\r\n"
            f"{server_error_content if server_error_content else f'<h1>500 Internal Server Error: {e}</h1>'}"
        )
        return status_code, response


async def work_with_client(reader, writer):
    client_address = writer.get_extra_info('peername')[0]
    while True:
        try:
            client_request = (await reader.read(10000)).decode()
            if not client_request:
                break

            print(f"Received: {client_request}")
            status_code, response_to_client = create_response(client_request)
            print(f"status code: {status_code}")

            # Log the HTTP request
            request_line = client_request.splitlines()[0]
            logs.log_http_request(request_line, client_address,
                                  f"{status_code}")

            # Determine if the response is bytes or string
            if isinstance(response_to_client, bytes):
                writer.write(response_to_client)
            else:
                writer.write(response_to_client.encode())

            await writer.drain()

            if 500 <= status_code < 600:
                print(f"Server error occurred with status {status_code}")

            # Handle Keep-Alive
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
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
            break

    writer.close()
    await writer.wait_closed()


async def start_multiple_servers():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    server1 = await asyncio.start_server(
        work_with_client,
        config["server"]["host"],
        443,
        ssl=ssl_context
    )

    # Создаём отдельный SSL-контекст для порта 8081, если необходимо
    ssl_context_8081 = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context_8081.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    server2 = await asyncio.start_server(
        work_with_client,
        config["server"]["host"],
        8081,
        ssl=ssl_context_8081  # Включаем SSL для порта 8081
    )

    async with server1, server2:
        await asyncio.gather(server1.serve_forever(), server2.serve_forever())


if __name__ == "__main__":
    asyncio.run(start_multiple_servers())
