import os
from pathlib import Path
from typing import List
from urllib.parse import quote
from urllib.request import urlopen, Request


PING_TIMEOUT_SECONDS = 5
PING_MAX_ATTEMPTS = 2


def _load_dotenv():
    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def _healthcheck_config():
    _load_dotenv()
    url_dest = os.environ.get("HEALTHCHECK_URL", "").rstrip("/")
    token = os.environ.get("HEALTHCHECK_TOKEN", "")
    if not url_dest or not token:
        raise RuntimeError(
            "Defina HEALTHCHECK_URL e HEALTHCHECK_TOKEN nas variaveis de ambiente."
        )
    return url_dest, token

def Healthcheck_ping(nome_servido: str) -> str:
    """Envia ping ao Healthcheck e considera falha somente apos duas tentativas."""
    try:
        url_dest, token = _healthcheck_config()
    except Exception as error:
        return str(error)

    errors: List[str] = []
    for _ in range(PING_MAX_ATTEMPTS):
        try:
            request = Request(
                f"{url_dest}/ping/{quote(nome_servido, safe='')}?token={quote(token, safe='')}",
                data=b"",
            )
            response = urlopen(request, timeout=PING_TIMEOUT_SECONDS)
            response_text = response.read().decode()
        except Exception as error:
            response_text = str(error)

        if response_text.strip() == "OK":
            return response_text
        errors.append(response_text)

    return "Falha no healthcheck apos 2 tentativas: " + " | ".join(errors)

if __name__ == "__main__":
    print(Healthcheck_ping("SERVICO_TESTE"))
