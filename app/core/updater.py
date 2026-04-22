import requests

def check_update(current_version: str) -> str | None:
    try:
        resp = requests.get(
            "https://api.github.com/repos/Mikhail-source/net_scanner/releases/latest",
            timeout=3
        )
        latest = resp.json()["tag_name"].lstrip("v")
        return latest if latest != current_version else None
    except:
        return None  # Не блокируем работу при ошибке проверки