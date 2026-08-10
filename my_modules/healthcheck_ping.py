import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen, Request


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

def Healthcheck_ping(nome_servido:str):
    ''' Envia ping ao servidor de Healthcheck para informar que o serviço está ativo '''
    try:
        url_dest, token = _healthcheck_config()
        req = Request(
            f"{url_dest}/ping/{quote(nome_servido, safe='')}?token={quote(token, safe='')}",
            data=b"",
        )
        response = urlopen(req, timeout=5)
        return response.read().decode()
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    print(Healthcheck_ping("SERVICO_TESTE"))
