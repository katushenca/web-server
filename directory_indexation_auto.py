import os
import datetime

def generate_directory_index(path):
    try:
        files = os.listdir(path)
        files.sort(key=lambda x: x.lower())
    except OSError:
        return "<h1>404 Not Found</h1>", 404

    # Формирование относительного пути для заголовка
    relative_path = os.path.relpath(path, os.getcwd())
    html = f"<html><head><title>Index of /{relative_path}</title></head><body>"
    html += f"<h1>Index of /{relative_path}</h1>"
    html += "<table><tr><th>Name</th><th>Last modified</th><th>Size</th></tr>"

    # Ссылка на родительский каталог
    if relative_path != ".":
        html += '<tr><td><a href="../">Parent Directory</a></td><td>-</td><td>-</td></tr>'

    for file in files:
        full_path = os.path.join(path, file)
        is_dir = os.path.isdir(full_path)
        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M")
        size = "-" if is_dir else f"{os.path.getsize(full_path) / (1024 * 1024):.1f}M"

        # Создание ссылки для перехода в подкаталог или скачивания файла
        href = f"{file}/" if is_dir else file
        html += f'<tr><td><a href="{href}">{file}</a></td><td>{last_modified}</td><td>{size}</td></tr>'

    html += "</table></body></html>"

    return html, 200
