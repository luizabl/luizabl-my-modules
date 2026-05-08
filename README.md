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

id_info    = Class_Mensagem_Log.id_msg(86400)   # re-envia no máximo 1x/dia
id_warning = Class_Mensagem_Log.id_msg(3600)
id_exc     = Class_Mensagem_Log.id_msg(300)

logger.info("Iniciando...", id=id_info)
logger.warning("Atenção!", id=id_warning)
logger.erro("Erro de usuário", id=id_info)
logger.critical("Erro inesperado", id=id_exc)
logger.exception("Exceção capturada", id=id_exc)

# Enviar pelo servidor de mensagens (Telegram/Pushbullet):
logger.info("Deploy concluído", id=id_info, EnviarServidorMsgs=True)
```

Quando `EnviarServidorMsgs=True`, a mensagem entregue segue o formato:

```
[CLASS_MSG_APP_NAME]
[TITULO]
Mensagem
[id_msg.id()]
```

A linha `[CLASS_MSG_APP_NAME]` é omitida se a variável de ambiente não estiver definida.

O parâmetro `id: id_msg` é obrigatório em todos os métodos e controla a frequência mínima de reenvio para o servidor de mensagens (em segundos).

O servidor de mensagens é auto-configurado via variáveis de ambiente:
- `TELEGRAM_TOKEN` + `TELEGRAM_CHAT_ID` — primário
- `PushBullet_APIKEY` — fallback
- `CLASS_MSG_APP_NAME` — nome da aplicação exibido nas mensagens enviadas

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
Envio de notificações via Pushbullet com controle global de frequência.

```python
from my_modules import Pushbullet_Class

pb = Pushbullet_Class.Pushbullet_Class()  # auto-configura via PushBullet_APIKEY
pb.PushbulletSendMsg("Mensagem")
pb.PushbulletSendMsg("Urgente", ForcarEnvio=True)  # ignora o intervalo mínimo
```

### `Telegram_Class`
Envio de mensagens via Telegram com controle global de frequência.

```python
from my_modules import Telegram_Class

tg = Telegram_Class.Telegram_Class()  # auto-configura via TELEGRAM_TOKEN e TELEGRAM_CHAT_ID
tg.TelegramSendMsg("Mensagem")
tg.TelegramSendMsg("Urgente", ForcarEnvio=True)  # ignora o intervalo mínimo
```

### `healthcheck_ping`
Ping para servidor de healthcheck para confirmar que um serviço está ativo.

```python
from my_modules.healthcheck_ping import Healthcheck_ping

resposta = Healthcheck_ping("NOME_DO_SERVICO")
```

## Variáveis de ambiente

| Variável               | Módulo                | Descrição                                          |
|------------------------|-----------------------|----------------------------------------------------|
| `TELEGRAM_TOKEN`       | `Telegram_Class`      | Token do bot Telegram                              |
| `TELEGRAM_CHAT_ID`     | `Telegram_Class`      | Chat ID do Telegram                                |
| `PushBullet_APIKEY`    | `Pushbullet_Class`    | API Key do Pushbullet                              |
| `CLASS_MSG_APP_NAME`   | `Class_Mensagem_Log`  | Nome da aplicação exibido nas mensagens enviadas   |

## Testes

```bash
pip install pytest
pytest tests/
```

Os testes estão divididos em **unitários** (sem dependências externas) e **de integração** (fazem chamadas reais às APIs).

Os testes de integração são pulados automaticamente (`SKIPPED`) quando as variáveis de ambiente necessárias não estão definidas no `.env`. Para rodá-los, preencha as variáveis correspondentes:

| Suite de integração     | Variáveis necessárias                          |
|-------------------------|------------------------------------------------|
| `Telegram_Class`        | `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`           |
| `Pushbullet_Class`      | `PushBullet_APIKEY`                            |
| `Class_Mensagem_Log`    | `TELEGRAM_TOKEN`+`TELEGRAM_CHAT_ID` ou `PushBullet_APIKEY` |
