# luizabl-my-modules

Módulos utilitários reutilizáveis para projetos Python.

## Instalação

```bash
pip install git+https://github.com/luizabl/luizabl-my-modules.git
```

Com suporte a notificações via Pushbullet:

```bash
pip install "git+https://github.com/luizabl/luizabl-my-modules.git#egg=luizabl-my-modules[pushbullet]"
```

## Módulos

### `DebugModeTester`
Detecta o modo de execução (debug, .exe, Jupyter) e define os paths do programa.

```python
from my_modules import DebugModeTester

print(DebugModeTester.application_path)   # path dos arquivos de dados
print(DebugModeTester.__debug_mode__)     # True se rodando em debug
```

### `Class_Mensagem_Log`
Logger com suporte a console, arquivo, PyQt5 e envio de alertas via Telegram/Pushbullet.

```python
from my_modules import Class_Mensagem_Log

logger = Class_Mensagem_Log.Class_Mensagem_Log("MeuModulo")
logger.info("Iniciando...")
logger.warning("Atenção!")
logger.erro("Erro de usuário")
logger.critical("Erro inesperado")
logger.exception("Exceção capturada", id=Class_Mensagem_Log.id_msg(86400))
```

O servidor de mensagens é auto-configurado via variáveis de ambiente:
- `TELEGRAM_TOKEN` + `TELEGRAM_CHAT_ID` — primário
- `PushBullet_APIKEY` — fallback

### `Class_Configuracoes`
Armazenamento e leitura de configurações em arquivo JSON.

```python
from my_modules import Class_Configuracoes

config = Class_Configuracoes.Class_Configuracoes("Configuracoes/config.json")
config.set_configuracao("MinhaClasse", "intervalo", 60)
intervalo = config.get_configuracao("MinhaClasse", "intervalo", ValueDefault=30)
```

### `DataFrame_Methodes`
Funções utilitárias para manipulação de DataFrames pandas.

```python
from my_modules import DataFrame_Methodes
import pandas as pd

df = pd.DataFrame(columns=["col1", "col2"])
df = DataFrame_Methodes.Pandas_add_row(df, {"col1": 1, "col2": 2})
df = DataFrame_Methodes.Pandas_add_rows(df, [{"col1": 3, "col2": 4}, {"col1": 5, "col2": 6}])
```

### `Pushbullet_Class`
Envio de notificações via Pushbullet com controle de frequência por motivo.

```python
from my_modules import Pushbullet_Class

pb = Pushbullet_Class.Pushbullet_Class()  # auto-configura via PushBullet_APIKEY
pb.PushbulletSendMsg("Titulo", "Mensagem", motivo="alerta")
```

### `Telegram_Class`
Envio de mensagens via Telegram com controle de frequência por motivo.

```python
from my_modules import Telegram_Class

tg = Telegram_Class.Telegram_Class()  # auto-configura via TELEGRAM_TOKEN e TELEGRAM_CHAT_ID
tg.TelegramSendMsg("Titulo", "Mensagem", motivo="alerta")
```

### `healthcheck_ping`
Ping para servidor de healthcheck para confirmar que um serviço está ativo.

```python
from my_modules.healthcheck_ping import Healthcheck_ping

resposta = Healthcheck_ping("NOME_DO_SERVICO")
```

## Variáveis de ambiente

| Variável           | Módulo            | Descrição                     |
|--------------------|-------------------|-------------------------------|
| `TELEGRAM_TOKEN`   | `Telegram_Class`  | Token do bot Telegram         |
| `TELEGRAM_CHAT_ID` | `Telegram_Class`  | Chat ID do Telegram           |
| `PushBullet_APIKEY`| `Pushbullet_Class`| API Key do Pushbullet         |

## Testes

```bash
pip install pytest
pytest tests/
```
