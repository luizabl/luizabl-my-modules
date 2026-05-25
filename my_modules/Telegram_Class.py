from . import DebugModeTester

import datetime as dt
import logging
import os
from urllib.request import urlopen
from urllib.parse import urlencode


VERSION_DEBUGMODETESTER_COMPATIBLE = "1.0.0"
if (DebugModeTester.__version__ != VERSION_DEBUGMODETESTER_COMPATIBLE):
    raise Exception(f"Versão incompatível: DebugModeTester.__version__ {DebugModeTester.__version__}. Versão compatível: {VERSION_DEBUGMODETESTER_COMPATIBLE}")


__version__ = "1.14.0"

#------------------------------------------------------------------------------------
#                                                                                   -
#                               Classe Telegram_Class                               -
#                                                                                   -
#------------------------------------------------------------------------------------

class Telegram_Class():
    '''
    Classe usada para enviar mensagens via Telegram.
    Auto-configura a partir das variáveis de ambiente TELEGRAM_TOKEN e TELEGRAM_CHAT_ID.
    Faz o controle global da frequência de envio (independente de motivo).
    '''
    logger = logging.getLogger(__name__)
    if (DebugModeTester.__debug_mode__):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    def __init__(self) -> None:
        self.__token   = None
        self.__chat_id = None
        self.__config  = None
        self.__UltimoEnvio = dt.datetime(1, 1, 1)
        self.__enviou_alerta_nao_configurado = False

        token   = os.environ.get("TELEGRAM_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if token and chat_id:
            self.TelegramSet(token, chat_id)

    def TelegramIsSet(self) -> bool:
        ''' Verifica se o Telegram já foi configurado. Se não estiver, tenta configurar via env. '''
        if self.__token is None or self.__chat_id is None:
            token   = os.environ.get("TELEGRAM_TOKEN", "")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
            if token and chat_id:
                self.TelegramSet(token, chat_id)
        return self.__token is not None and self.__chat_id is not None

    def TelegramSet(self, token: str, chat_id: str, IntervaloMinimo_seg: int = 10):
        '''
        Configura o token e chat_id do Telegram.
        Também define o intervalo mínimo global entre envios, com no mínimo 1 seg.
        '''
        if IntervaloMinimo_seg < 1:
            raise ValueError("IntervaloMinimo_seg deve ser >= 1")

        self.__UltimoEnvio = dt.datetime(1, 1, 1)
        self.__config  = {"IntervaloMinimo_seg": IntervaloMinimo_seg}
        self.__token   = token
        self.__chat_id = chat_id

    def TelegramSendMsg(self, msg: str, ForcarEnvio: bool = False, parse_mode: str | None = None):
        '''
        Envia uma mensagem via Telegram desde que passado o tempo IntervaloMinimo_seg
        desde o último envio (controle global, independente de motivo).

        parse_mode: opcional. Valores aceitos pela API do Telegram: "Markdown", "MarkdownV2", "HTML".
        '''
        if not self.TelegramIsSet():
            if not self.__enviou_alerta_nao_configurado:
                self.logger.critical("Telegram não configurado — alertas não serão enviados.")
                self.__enviou_alerta_nao_configurado = True
            return

        if type(msg) != str:
            raise TypeError("msg deve ser str")

        segundos = (dt.datetime.now() - self.__UltimoEnvio).total_seconds()
        if segundos >= self.__config["IntervaloMinimo_seg"] or ForcarEnvio:
            payload = {"chat_id": self.__chat_id, "text": msg}
            if parse_mode is not None:
                payload["parse_mode"] = parse_mode
            data = urlencode(payload).encode()
            urlopen(
                f"https://api.telegram.org/bot{self.__token}/sendMessage",
                data=data,
                timeout=5,
            )
            self.__UltimoEnvio = dt.datetime.now()
