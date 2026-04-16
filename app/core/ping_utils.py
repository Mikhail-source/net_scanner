import asyncio
import platform

async def async_ping(host: str, timeout: float = 1.0) -> bool:
    """
    Асинхронный ping хоста.
    Возвращает True, если хост отвечает.
    """
    # Определяем параметр количества пакетов в зависимости от ОС
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    # Команда: 1 пакет, таймаут
    command = ['ping', param, '1', '-W', str(int(timeout * 1000)), host]
    if platform.system().lower() == 'windows':
        command = ['ping', '-n', '1', '-w', str(int(timeout * 1000)), host]

    try:
        # Запускаем процесс
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Ждём завершения с таймаутом
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout + 0.5)
        
        # Возвращаем код завершения: 0 = успех
        return process.returncode == 0
    except asyncio.TimeoutError:
        return False
    except Exception:
        return False