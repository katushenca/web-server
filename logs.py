import logging


logging.basicConfig(filename='logs/http_requests.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')


def parse_http_request(request):
    lines = request.split('\n')
    method, url, http_version = lines[0].strip().split()
    headers = {}
    for line in lines[1:]:
        line = line.strip()
        if line:
            key, value = line.split(': ', 1)
            headers[key] = value
    return method, url, http_version, headers


def log_http_request(request):
    method, url, http_version, headers = parse_http_request(request)
    logging.debug(f'{method} {url} {http_version}')
    for key, value in headers.items():
        logging.debug(f'{key}: {value}')
