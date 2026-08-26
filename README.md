# luizabl-my-modules

Módulos utilitários reutilizáveis para projetos Python.

## Instalação

```bash
pip install git+https://github.com/luizabl/luizabl-my-modules.git
```

Com dependências opcionais:

```bash
# Suporte a pandas (DataFrame_Methodes)
pip install "git+https://github.com/luizabl/luizabl-my-modules.git#egg=luizabl-my-modules[pandas]"

# Suporte a notificações via Pushbullet
pip install "git+https://github.com/luizabl/luizabl-my-modules.git#egg=luizabl-my-modules[pushbullet]"

# Suporte a PyQt5
pip install "git+https://github.com/luizabl/luizabl-my-modules.git#egg=luizabl-my-modules[qt]"

# Tudo junto
pip install "git+https://github.com/luizabl/luizabl-my-modules.git#egg=luizabl-my-modules[pandas,pushbullet,qt]"
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

O arquivo `app.log` usa um handler compartilhado entre os loggers do processo.
Na virada do dia, o arquivo atual é fechado e substituído imediatamente; o
conteúdo encerrado é compactado em segundo plano como
`logs_historicos/app-AAAA-MM-DD.log.gz`. Compactações interrompidas ficam com
extensão `.pending` e são retomadas na próxima inicialização.

Para consultar as últimas linhas sem carregar o arquivo inteiro:

```python
from my_modules.log_historico import ler_log_aplicacao

atual = ler_log_aplicacao(quantidade=50)
historico = ler_log_aplicacao(quantidade=50, data="2026-08-09")
```

`quantidade` deve estar entre 1 e 500. A leitura histórica aceita apenas datas
no formato `YYYY-MM-DD` e nunca recebe um caminho fornecido pelo cliente.

O servidor de mensagens é auto-configurado via variáveis de ambiente:
- `TELEGRAM_TOKEN` + `TELEGRAM_CHAT_ID` — primário
- `PushBullet_APIKEY` — fallback
- `CLASS_MSG_APP_NAME` — nome da aplicação exibido nas mensagens enviadas

Se apenas uma credencial do Telegram estiver presente, o logger registra uma vez
por processo qual variável está ausente e envia o aviso pelo Pushbullet, quando
disponível. Se o Telegram falhar com as duas credenciais configuradas, o motivo
do erro e o fallback para Pushbullet também são registrados e notificados uma
única vez por processo.

Durante a implementação de mudanças em `my_modules/Class_Mensagem_Log.py`, não
execute os testes de envio real para Telegram e Pushbullet, para não poluir os
canais de mensagens. Porém, antes de criar um commit que modifique
`Class_Mensagem_Log.py`, execute explicitamente esses dois testes para confirmar
que os envios continuam funcionando. No PowerShell, use:

```powershell
$env:RUN_REAL_MESSAGE_TESTS = "1"
.\.venv\Scripts\python.exe -m pytest tests\Class_Mensagem_Log\integracao -q
Remove-Item Env:RUN_REAL_MESSAGE_TESTS
```

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
tg.TelegramSendMsg("Urgente", ForcarEnvio=True)       # ignora o intervalo mínimo
tg.TelegramSendMsg("*Negrito*", parse_mode="Markdown") # formatação: "Markdown", "MarkdownV2" ou "HTML"
# Se o parse_mode for rejeitado pela API (ex: underscore solto), a mensagem é reenviada sem formatação.
```

### `healthcheck_ping`
Ping para servidor de healthcheck para confirmar que um serviço está ativo.

```python
from my_modules.healthcheck_ping import Healthcheck_ping

resposta = Healthcheck_ping("NOME_DO_SERVICO")
```

Cada envio faz no maximo duas tentativas imediatas. Uma resposta `OK` em
qualquer tentativa confirma o ping; somente duas falhas retornam erro, com os
motivos das duas tentativas no texto retornado.

## Variáveis de ambiente

| Variável               | Módulo                | Descrição                                          |
|------------------------|-----------------------|----------------------------------------------------|
| `TELEGRAM_TOKEN`       | `Telegram_Class`      | Token do bot Telegram                              |
| `TELEGRAM_CHAT_ID`     | `Telegram_Class`      | Chat ID do Telegram                                |
| `PushBullet_APIKEY`    | `Pushbullet_Class`    | API Key do Pushbullet                              |
| `CLASS_MSG_APP_NAME`   | `Class_Mensagem_Log`  | Nome da aplicação exibido nas mensagens enviadas   |

Para configurar o `healthcheck_ping`, defina estas variaveis no `.env` da aplicacao
ou no ambiente do processo:

```dotenv
HEALTHCHECK_URL=https://www.criciumajogos.com.br/healthcheck
HEALTHCHECK_TOKEN=replace-with-the-healthcheck-token
```

| Variavel | Modulo | Descricao |
|----------|--------|-----------|
| `HEALTHCHECK_URL` | `healthcheck_ping` | URL base do servidor de Healthcheck |
| `HEALTHCHECK_TOKEN` | `healthcheck_ping` | Token enviado somente no header HTTPS `X-Healthcheck-Token` |

O teste de integracao do Healthcheck envia um ping real para `SERVICO_TESTE` apenas
quando `HEALTHCHECK_URL` e `HEALTHCHECK_TOKEN` estiverem definidos; sem essas
variaveis, ele fica marcado como `SKIPPED`.

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
