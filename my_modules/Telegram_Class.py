from . import DebugModeTester

import datetime as dt
import logging
import os
from urllib.request import urlopen
from urllib.parse import urlencode


VERSION_DEBUGMODETESTER_COMPATIBLE = "1.0.0"
if (DebugModeTester.__version__ != VERSION_DEBUGMODETESTER_COMPATIBLE):
    raise Exception(f"Versão incompatível: DebugModeTester.__version__ {DebugModeTester.__version__}. Versão compatível: {VERSION_DEBUGMODETESTER_COMPATIBLE}")


__version__ = "1.0.0"

#------------------------------------------------------------------------------------
#                                                                                   -
#                               Classe Telegram_Class                               -
#                                                                                   -
#------------------------------------------------------------------------------------

class Telegram_Class():
    '''
    Classe usada para enviar mensagens via Telegram.
    Auto-configura a partir das variáveis de ambiente TELEGRAM_TOKEN e TELEGRAM_CHAT_ID.
    Também faz o controle da frequência de envio por motivo.
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
        self.__UltimoEnvio: dict = {}
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
        Também define o intervalo mínimo entre envios do mesmo motivo, com no mínimo 1 seg.
        '''
        if IntervaloMinimo_seg < 1:
            raise ValueError("IntervaloMinimo_seg deve ser >= 1")

        data_zero = dt.datetime(1, 1, 1)
        self.__UltimoEnvio = {
            k: data_zero for k in
            ("exception", "critical", "erro", "warning", "info", "debug")
        }
        self.__config  = {"IntervaloMinimo_seg": IntervaloMinimo_seg}
        self.__token   = token
        self.__chat_id = chat_id

    def TelegramSendMsg(self, titulo: str, msg: str,
                        motivo: str = None, ForcarEnvio: bool = False):
        '''
        Envia uma mensagem via Telegram desde que passado o tempo IntervaloMinimo_seg
        desde o último envio daquele motivo.

        motivo pode ser qualquer string que identifique o tipo da mensagem para
        evitar envio excessivo da mesma mensagem.
        '''
        if not self.TelegramIsSet():
            if not self.__enviou_alerta_nao_configurado:
                self.logger.critical("Telegram não configurado — alertas não serão enviados.")
                self.__enviou_alerta_nao_configurado = True
            return

        if type(msg) != str:
            raise TypeError("msg deve ser str")
        if motivo is None:
            raise ValueError("motivo não pode ser None")

        if motivo not in self.__UltimoEnvio:
            self.__UltimoEnvio[motivo] = dt.datetime(1, 1, 1)

        segundos = (dt.datetime.now() - self.__UltimoEnvio[motivo]).total_seconds()
        if segundos >= self.__config["IntervaloMinimo_seg"] or ForcarEnvio:
            texto = f"{titulo}\n{msg}"
            data = urlencode({"chat_id": self.__chat_id, "text": texto}).encode()
            urlopen(
                f"https://api.telegram.org/bot{self.__token}/sendMessage",
                data=data,
                timeout=5,
            )
            self.__UltimoEnvio[motivo] = dt.datetime.now()
