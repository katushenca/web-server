import asyncio
import logs
import json
import ssl
import os
from pathlib import Path
import directory_indexation_auto


with open('config.json', 'r') as config_file:
    config = json.load(config_file)


file_cache = {}
directory_cache = {}
MAX_CACHE_SIZE = 100

def read_html_file(file_path):
    global file_cache
    path = Path(file_path)
    if not path.exists():
        return None
    last_modified = path.stat().st_mtime

    cached = file_cache.get(file_path)
    if cached:
        cached_content, cached_mtime = cached
        if cached_mtime == last_modified:
            return cached_content

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        print('file_cache', file_cache)
        file_cache[file_path] = (content, last_modified)
        if len(file_cache) > MAX_CACHE_SIZE:
            file_cache.pop(next(iter(file_cache)))
        return content
    except FileNotFoundError:
        return None

def read_binary_file(file_path):
    global file_cache
    path = Path(file_path)
    if not path.exists():
        return None

    last_modified = path.stat().st_mtime

    # Проверка кэша
    cached = file_cache.get(file_path)
    if cached:
        cached_content, cached_mtime = cached
        if cached_mtime == last_modified:
            return cached_content
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
        file_cache[file_path] = (content, last_modified)
        if len(file_cache) > MAX_CACHE_SIZE:
            file_cache.pop(next(iter(file_cache)))
        return content
    except FileNotFoundError:
        return None

def get_directory_index(local_path):
    global directory_cache

    path = Path(local_path)
    if not path.exists() or not path.is_dir():
        return "", 404

    last_modified = path.stat().st_mtime
    cached = directory_cache.get(local_path)
    if cached:
        cached_content, cached_mtime = cached
        if cached_mtime == last_modified:
            return cached_content, 200
    try:
        html_content, status_code = directory_indexation_auto.generate_directory_index(local_path)
        directory_cache[local_path] = (html_content, last_modified)
        if len(directory_cache) > MAX_CACHE_SIZE:
            directory_cache.pop(next(iter(directory_cache)))
        return html_content, status_code
    except Exception as e:
        print(f"Error generating directory index for {local_path}: {e}")
        return "", 500




def get_host(request):
    for line in request.split('\r\n'):
        if line.lower().startswith('host:'):
            return line.split(':', 1)[1].strip()
    return 'localhost'

def create_response(request):
    path = request.split()[1]
    status_code = 200
    try:
        local_path = os.path.join(os.getcwd(), path.lstrip('/'))
        print(local_path, 'fsdfsdfs')
        if os.path.isdir(local_path):
            html_content, status_code = get_directory_index(local_path)
            response = f"HTTP/1.1 {status_code} OK\r\nContent-Type: text/html\r\n\r\n{html_content}"
            return status_code, response

        if os.path.isfile(local_path):
            file_name = os.path.basename(local_path)
            file_data = read_binary_file(local_path)
            if file_data is None:
                raise FileNotFoundError

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
            html_content = read_html_file("html_files/other.html")
            response = f"HTTP/1.1 {status_code} OK\r\nContent-Type: text/html\r\n\r\n{html_content}"
            return status_code, response

        if path in ["/home", "/lizka"]:
            html_content = read_html_file(f"html_files/{path.lstrip('/')}.html")
        elif path == '/':
            html_content = read_html_file("html_files/hello.html")
        elif path == '/katya':
            html_content = read_html_file("html_files/katya.html")
        else:
            html_content = None

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

    except FileNotFoundError:
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

async def work_with_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    client_address = writer.get_extra_info('peername')[0]
    while True:
        try:
            client_request = (await reader.read(10000)).decode()
            if not client_request:
                break

            print(f"Received: {client_request}")
            status_code, response_to_client = create_response(client_request)
            print(f"status code: {status_code}")

            # Логирование HTTP-запроса
            request_line = client_request.splitlines()[0]
            logs.log_http_request(request_line, client_address, f"{status_code}")

            # Определение типа ответа (строка или байты)
            if isinstance(response_to_client, bytes):
                writer.write(response_to_client)
            else:
                writer.write(response_to_client.encode())

            await writer.drain()

            if 500 <= status_code < 600:
                print(f"Server error occurred with status {status_code}")

            if config.get("keep-alive", {}).get("using", "false").lower() != "true":
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
        ssl=ssl_context_8081
    )

    async with server1, server2:
        await asyncio.gather(server1.serve_forever(), server2.serve_forever())

if __name__ == "__main__":
    asyncio.run(start_multiple_servers())
