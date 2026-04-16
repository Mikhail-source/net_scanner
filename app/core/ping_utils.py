import asyncio
import platform
import sys

async def async_ping(host: str, timeout: float = 1.0) -> bool:
    """Асинхронный ping хоста"""
    system = platform.system().lower()
    
    if system == 'windows':
        # Windows: -n (count), -w (timeout in ms)
        command = ['ping', '-n', '1', '-w', str(int(timeout * 1000)), host]
    else:
        # Linux/Mac: -c (count), -W (timeout in seconds, float!)
        command = ['ping', '-c', '1', '-W', str(timeout), host]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=timeout + 1.0
        )
        return process.returncode == 0
    except asyncio.TimeoutError:
        return False
    except FileNotFoundError:
        # Утилита ping не найдена
        print(f"Warning: 'ping' command not found", file=sys.stderr)
        return False
    except Exception:
        return False