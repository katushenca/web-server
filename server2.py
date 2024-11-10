import server as s
import asyncio

async def server2(port):
    server = await asyncio.start_server(
        s.work_with_client,
        s.config["server"]["host"],
        port,  # Указываем порт для второго сервера
    )
    async with server:
        print("cервер запущен навсегда")
        await server.serve_forever()

asyncio.run(server2(8081))