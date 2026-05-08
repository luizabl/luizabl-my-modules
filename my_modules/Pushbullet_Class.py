from . import DebugModeTester

import datetime as dt
import os
from time import sleep
from pushbullet import Pushbullet #pushbullet.py==0.12.0
import logging


VERSION_DEBUGMODETESTER_COMPATIBLE = "1.0.0"
if (DebugModeTester.__version__ != VERSION_DEBUGMODETESTER_COMPATIBLE):
    raise Exception(f"Versão incompatível: DebugModeTester.__version__ {DebugModeTester.__version__}. Versão compatível: {VERSION_DEBUGMODETESTER_COMPATIBLE}")


__version__ = "1.0.0"

#------------------------------------------------------------------------------------
#                                                                                   -
#                              Classe Pushbullet_Class                              -
#                                                                                   -
#------------------------------------------------------------------------------------

class Pushbullet_Class():
    '''
    Classe usada para enviar mensagens pushbullet.
    Faz o controle global da frequência de envio (independente de motivo).
    '''
    logger = logging.getLogger(__name__)
    if (DebugModeTester.__debug_mode__):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    def __init__(self,API_KEY=None) -> None:

        self.__Pushbulletmotor = None
        self.__Pushbulletmotor_config = None
        self.__Pushbulletmotor_UltimoEnvio = dt.datetime(1, 1, 1)

        self.__Pushbulletmotor_enviou_mensagem_alerta_nao_configurado = False

        api_key = API_KEY or os.environ.get("PushBullet_APIKEY", "")
        if api_key:
            self.PushbulletSet(api_key)


    def PushbulletIsSet(self):
        ''' Verifica se o pushbullet já foi configurado. Se não estiver, tenta configurar via env. '''
        if self.__Pushbulletmotor is None:
            api_key = os.environ.get("PushBullet_APIKEY", "")
            if api_key:
                self.PushbulletSet(api_key)
        return self.__Pushbulletmotor is not None

    def Pushbullet_API_KEY_Get(self):
        ''' Retorna a API_KEY do pushbullet '''
        if (self.__Pushbulletmotor is None):
            return ""
        else:
            return self.__Pushbulletmotor.api_key

    def PushbulletSet(self,Pushbullet_API_KEY:str=None,IntervaloMinimo_seg=10):
        '''
        Define a API_KEY do pushbullet para enviar mensagens para o celular.

        Se não for definida uma API_KEY, não serão enviadas as mensagens via pushbullet

        Também define o intervalo mínimo global entre envios de pushbullet, com no mínimo 1seg.

        Se não foi passado uma API_KEY para o logger Root, será passada a primeira API_KEY que for definida também para o Root

        '''

        if (IntervaloMinimo_seg<1):
            raise ValueError("O intervalo mínimo entre os envios de pushbullet deve ser de pelo menos 1 segundo")

        self.__Pushbulletmotor_UltimoEnvio = dt.datetime(1, 1, 1)
        self.__Pushbulletmotor_config = {"IntervaloMinimo_seg":IntervaloMinimo_seg}

        if (Pushbullet_API_KEY is not None):
            if (self.__Pushbulletmotor is None):
                self.__Pushbulletmotor = Pushbullet(Pushbullet_API_KEY)
            elif (self.__Pushbulletmotor.api_key != Pushbullet_API_KEY):
                self.__Pushbulletmotor = Pushbullet(Pushbullet_API_KEY)


    def PushbulletSendMsg(self, msg: str, ForcarEnvio: bool = False):
        ''' Envia uma mensagem via pushbullet para o celular desde que passado o tempo
        self.__Pushbulletmotor_config["IntervaloMinimo_seg"] desde o último envio
        (controle global, independente de motivo).
        '''
        if (self.__Pushbulletmotor is not None):

            if (type(msg) != str):
                raise TypeError("A mensagem deve ser uma string")

            SegundosDesteUltimoEnvio = (dt.datetime.now() - self.__Pushbulletmotor_UltimoEnvio).total_seconds()

            if (SegundosDesteUltimoEnvio>=self.__Pushbulletmotor_config["IntervaloMinimo_seg"] or ForcarEnvio):
                try:
                    self.__Pushbulletmotor.push_note("", msg)
                except:
                    sleep(5)
                    self.__Pushbulletmotor.push_note("", msg)
                self.__Pushbulletmotor_UltimoEnvio = dt.datetime.now()
        elif not self.__Pushbulletmotor_enviou_mensagem_alerta_nao_configurado:
            self.logger.critical("Não foi configurada nenhuma Pushbullet API_KEY! Não serão enviados alertas via pushbullet!")
            self.__Pushbulletmotor_enviou_mensagem_alerta_nao_configurado = True
