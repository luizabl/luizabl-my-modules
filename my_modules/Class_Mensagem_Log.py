
#------------------------------------------------------------------------------------
#                                                                                   -
#                               Class_Mensagem_Log                                  -
#                                                                                   -
#------------------------------------------------------------------------------------


# O módulo logging verifica qual o path tá chamando o log quando se tenta mostrar a linha
# e para não retornar a linha do próprio módulo logging, ele pula quando o path da linha
# é o path do módulo. Porém como eu estou criando o logging dentro de outro módulo para
# ser utilizando em um terceiro, acontece que o primeiro path que aparece não é o do módulo
# loggin e sim o path do módulo Leal... Então precisa modificar qual o path que deve ser
# ignorado para que ele reflita o do módulo Leal

from. import DebugModeTester

import logging
import os
import sys
import inspect
import datetime as dt
import time
try:
    # PyQt5==5.15.10
    from PyQt5.QtWidgets import QTextBrowser, QWidget, QStatusBar
    from PyQt5.QtCore import pyqtSignal
    PYQT5_IMPORTADO = True
except:
    PYQT5_IMPORTADO = False

try:
    #pandas==2.1.0
    import pandas as pd
    PANDAS_IMPORTADO = True
except:
    PANDAS_IMPORTADO = False



VERSION_DEBUGMODETESTER_COMPATIBLE = "1.0.0"
if (DebugModeTester.__version__ != VERSION_DEBUGMODETESTER_COMPATIBLE):
    raise Exception(f"Versão incompatível: DebugModeTester.__version__ {DebugModeTester.__version__}. Versão compatível: {VERSION_DEBUGMODETESTER_COMPATIBLE}")

try:
    from . import Telegram_Class
    VERSION_TELEGRAMCLASS_COMPATIBLE = "1.0.0"
    if (Telegram_Class.__version__ != VERSION_TELEGRAMCLASS_COMPATIBLE):
        raise Exception(f"Versão incompatível: Telegram_Class.__version__ {Telegram_Class.__version__}. Versão compatível: {VERSION_TELEGRAMCLASS_COMPATIBLE}")
    TELEGRAM_IMPORTADO = True
except Exception as erro:
    TELEGRAM_IMPORTADO = False

try:
    from . import Pushbullet_Class
    VERSION_PUSHBULLETCLASS_COMPATIBLE = "1.0.0"
    if (Pushbullet_Class.__version__ != VERSION_PUSHBULLETCLASS_COMPATIBLE):
        raise Exception(f"Versão incompatível: Pushbullet_Class.__version__ {Pushbullet_Class.__version__}. Versão compatível: {VERSION_PUSHBULLETCLASS_COMPATIBLE}")
    PUSHBULLET_IMPORTADO = True
except Exception as erro:
    PUSHBULLET_IMPORTADO = False


__version__ = "1.0.0"

from .enum_timeframes import PERIOD_H1

_CLASS_MSG_APP_NAME = os.environ.get("CLASS_MSG_APP_NAME", "")


class id_msg:
    """Identifica um ponto de chamada de exception e define a frequência mínima de envio via servidor_msgs."""

    def __init__(self, frequencia_seg: int = 0, line=None, file=None, function=None):
        if frequencia_seg is None:
            raise ValueError("frequencia_seg cannot be None")
        if not isinstance(frequencia_seg, int):
            raise ValueError("frequencia_seg must be an int")
        if frequencia_seg < 0:
            raise ValueError("frequencia_seg must be >= 0")
        if (line is not None) and (file is None):
            raise ValueError("line requires file")
        if (file is not None) and (line is None):
            raise ValueError("file requires line")
        if (line is not None or file is not None) and function is not None:
            raise ValueError("Provide (line + file) or function, not both")

        # Auto-captura linha e arquivo do frame chamador quando nenhum identificador é fornecido
        if line is None and file is None and function is None:
            frame = inspect.currentframe().f_back
            line = frame.f_lineno
            file = frame.f_code.co_filename

        self.__frequencia_seg = frequencia_seg
        self.__line           = line
        self.__file           = os.path.basename(file) if file is not None else None
        self.__function       = function

    @property
    def frequencia_seg(self) -> int:
        return self.__frequencia_seg

    def id(self) -> str:
        if self.__line is not None:
            return f"|line|_{self.__line}_|file|_{self.__file}"
        return f"|func|_{self.__function}"


logging._srcfile = os.path.normcase(__file__)

class Class_Mensagem_Log():
    '''
    Cria um logger.
    As mesagens serão escritas no formato [%(name)s][line:%(lineno)d][%(asctime)s]: %(message)
    O logger tem a capacidade de:
        - Escrever na tela;
        - Escrever no arquivo;
        - Escrever em um QTextBrowser de PYQT5

    OBS: A parte [line:%(lineno)d] não funciona para programas em .exe


    Também é possível enviar as mensagens para um celular usando o servidor de mensagens.
    O servidor primário é o Telegram (auto-configurado via env TELEGRAM_TOKEN e TELEGRAM_CHAT_ID).
    Como fallback é usado o Pushbullet (auto-configurado via env PushBullet_APIKEY).
    Por padrão será enviada mensagem via servidor_msgs apenas para as exceptions.
    Para enviar uma mensagem exclusivamente via servidor_msgs, sem gravar logger, use o método self.servidor_msgs_SendMsg(msg)
    '''

    if TELEGRAM_IMPORTADO:
        __servidor_msgs_telegram = Telegram_Class.Telegram_Class()
    else:
        __servidor_msgs_telegram = None

    if PUSHBULLET_IMPORTADO:
        __servidor_msgs_pushbullet = Pushbullet_Class.Pushbullet_Class()
    else:
        __servidor_msgs_pushbullet = None

    AvisoServidorMsgNaoConfigurado_mostrado = False
    SERVIDOR_MSGS_ultima_msg_enviada_time = 0
    SERVIDOR_MSGS_tempo_minimo_entre_envios_s = 5
    ultimo_envio_msg_exception_ids: dict = {}  # dict[str, datetime]

    def __init__(self,__name__:str=None):
        '''
        - __name__ é o nome do arquivo que será mostrado quando se gera o logger para identificar de onde veio a mensagem

        Sugere-se que __name__ sejá self.__class__.__name__, porém ele pode ser qualquer nome que o usuário determine

        '''

        self.__CriarLogger(__name__)

        self.QTextBrowser_connected = False
        self.QStatusBar_connected = False
        self.ultima_msg_erro = time.time()

    def servidor_msgs_PushbulletSet(self, Pushbullet_API_KEY: str, IntervaloMinimo_seg=10):
        ''' Define a API_KEY do Pushbullet para usar como fallback no envio de mensagens '''
        if(not PUSHBULLET_IMPORTADO):
            raise Exception("O módulo Pushbullet não foi importado")
        self.__servidor_msgs_pushbullet.PushbulletSet(Pushbullet_API_KEY, IntervaloMinimo_seg)

    def _formatar_msg_servidor(self, titulo: str, msg: str, id: 'id_msg') -> str:
        partes = []
        if _CLASS_MSG_APP_NAME:
            partes.append(f"[{_CLASS_MSG_APP_NAME}]")
        partes.append(f"[{titulo}]")
        partes.append(str(msg))
        partes.append(f"[{id.id()}]")
        return "\n".join(partes)

    def servidor_msgs_SendMsg(self, msg: str, ForcarEnvio: bool = False):
        ''' Envia uma mensagem via servidor de mensagens. Prioriza Telegram; usa Pushbullet como fallback '''
        if (time.time() - Class_Mensagem_Log.SERVIDOR_MSGS_ultima_msg_enviada_time
                <= Class_Mensagem_Log.SERVIDOR_MSGS_tempo_minimo_entre_envios_s):
            return

        Class_Mensagem_Log.SERVIDOR_MSGS_ultima_msg_enviada_time = time.time()

        # Primário: Telegram
        if (TELEGRAM_IMPORTADO and self.__servidor_msgs_telegram is not None
                and self.__servidor_msgs_telegram.TelegramIsSet()):
            try:
                self.__servidor_msgs_telegram.TelegramSendMsg(msg, ForcarEnvio)
                return
            except Exception:
                pass  # cai no fallback

        # Fallback: Pushbullet
        if (PUSHBULLET_IMPORTADO and self.__servidor_msgs_pushbullet is not None
                and self.__servidor_msgs_pushbullet.PushbulletIsSet()):
            try:
                self.__servidor_msgs_pushbullet.PushbulletSendMsg(msg, ForcarEnvio)
            except Exception as e:
                if (e.args[0].find("pushbullet_pro_required") >= 0):
                    # Extrapolou o limite de envios mensais do pushbullet — desabilita
                    self.__servidor_msgs_pushbullet._Pushbullet_Class__Pushbulletmotor = None
                    if time.time() - self.ultima_msg_erro > 60 * 60:
                        print(e)
                    return
                raise e

    def servidor_msgs_IsSet(self) -> bool:
        ''' Verifica se algum servidor de mensagens está configurado (Telegram ou Pushbullet) '''
        telegram_ok = (TELEGRAM_IMPORTADO
                       and self.__servidor_msgs_telegram is not None
                       and self.__servidor_msgs_telegram.TelegramIsSet())
        pushbullet_ok = (PUSHBULLET_IMPORTADO
                         and self.__servidor_msgs_pushbullet is not None
                         and self.__servidor_msgs_pushbullet.PushbulletIsSet())
        return telegram_ok or pushbullet_ok

    def servidor_msgs_NotSetedMsError(self, RaseExeptionSeNaoImportado=True):
        ''' Mostra uma mensagem de erro informando que nenhum servidor de mensagens foi configurado.
         O aviso só é mostrado uma única vez para não floodar a tela com mensagens de erro'''

        if not self.AvisoServidorMsgNaoConfigurado_mostrado:
            self.AvisoServidorMsgNaoConfigurado_mostrado = True
            if (not TELEGRAM_IMPORTADO and not PUSHBULLET_IMPORTADO and RaseExeptionSeNaoImportado):
                raise Exception("Nenhum módulo de servidor de mensagens foi importado")
            print("------------------------------------------------------------------")
            print("Nenhum servidor de mensagens foi configurado!\nConfigure o Telegram via env TELEGRAM_TOKEN/TELEGRAM_CHAT_ID ou o Pushbullet via env PushBullet_APIKEY!")
            print("------------------------------------------------------------------")


    def __CriarLogger(self,__name__:str=None):
        '''
        Executa a criacao do logger
        - __name__ é o nome do arquivo que será mostrado quando se gera o logger para identificar de onde veio a mensagem

        Sugere-se que __name__ sejá o nome da classe que o logger faz parte ou outro nome que facilite a identificação do logger

        '''
        Logger_novo = True
        if(__name__ in logging.Logger.manager.loggerDict):
            Logger_novo = False
        if(__name__ is None):
            self.logger = logging.getLogger(inspect.stack()[1][0].f_locals.get("self", None).__class__.__name__)
        else:
            self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        #Só cria o handle se o logger não existir pois senão vai ficar duplicando as mensagens
        if(Logger_novo):

            # Create handlers
            # Default handler - Print messages to console, show mensage to PYQT5 elements and write to log file
            if (DebugModeTester.__debug_mode__):
                f_handler = logging.FileHandler(DebugModeTester.application_path+'\\app.log')
                f_handler.setLevel("DEBUG")
                # DEBUG handler - Only work in debug mode
                d_handler = logging.StreamHandler()
                d_handler.setLevel("DEBUG")
            else:
                f_handler = logging.FileHandler(DebugModeTester.application_path+'\\app.log')
                f_handler.setLevel("DEBUG")
                # DEBUG handler - Only work in debug mode
                d_handler = logging.StreamHandler()
                d_handler.setLevel("INFO")


            # Create formatters and add it to handlers
            # Este módulo é otimizado para funcionar com python até 3.9
            # Acima de 3.9 ele pode apresentar imprecisões, principalmente no Class_Mensagens
            # Então nas versões acima de 3.9 o número da linha é desabilitado do Class_Mensagens
            if sys.version_info < (3, 10):
                handler_format = logging.Formatter('[%(name)s][line:%(lineno)d][%(asctime)s] %(message)s')
            else:
                handler_format = logging.Formatter('[%(name)s][%(asctime)s] %(message)s')

            f_handler.setFormatter(handler_format)
            d_handler.setFormatter(handler_format)

            # Add handlers to the logger
            self.logger.addHandler(f_handler)
            self.logger.addHandler(d_handler)

    def connectQTextBrowser(self, Painel_de_texto):
        ''' Serve para que o logger mostre as mensagens no QTextBrowser de PYQT5 '''

        if (Painel_de_texto is None):
            return

        if (isinstance(Painel_de_texto) != QTextBrowser):
            raise TypeError("Painel_de_texto deve ser um QTextBrowser")

        #1- Para se enviar sinais no PYQT5 precisa ser uma subclasse de QWidget
        class Class_to_connect_to_QTextBrowser(QWidget):
            signal_ = pyqtSignal(str) #Sinal para transmitir o texto que é para aparecer no painel de texto
            signal_2 = pyqtSignal(int) #Sinal para tranmitir a posição que o cursos deve ir (para mover o cursor to the end)
            def __init__(self):
                super().__init__(None)

        self.signal_QtextBrowser = Class_to_connect_to_QTextBrowser()

        #2- Criando uma função no Painel_de_texto que mova o cursos para um determinado valor (que geralmente será o final do texto)
        Painel_de_texto.go_to_end = lambda valor: self.QTextBrowser.verticalScrollBar().setValue(valor)

        #3- É preciso guarda a referencia para que depois seja possível pegar qual o tamanho do painel_de_texto para poder
        #   definir que o ponteiro dele vá para o final do texto
        self.QTextBrowser = Painel_de_texto

        #4- Conectando os sinais criados com o painel de texto
        self.signal_QtextBrowser.signal_.connect(self.QTextBrowser.append)
        self.signal_QtextBrowser.signal_2.connect(self.QTextBrowser.go_to_end)

        #5- Marcando para o logger que existe um painel de texto para serem mostradas as mensagens
        self.QTextBrowser_connected = True

    def connectQStatusBar(self, StatusBar):
        ''' Serve para que o logger mostre as mensagens no QStatusBar de PYQT5 '''

        if (StatusBar is None):
            return
        if (isinstance(StatusBar) != QStatusBar):
            raise TypeError("StatusBar deve ser um QStatusBar")

        #1- Para se enviar sinais no PYQT5 precisa ser uma subclasse de QWidget
        class Class_to_connect_to_QStatusBar(QWidget):
            signal_ = pyqtSignal(str) #Sinal para transmitir o texto que é para aparecer no painel de texto
            def __init__(self):
                super().__init__(None)

        self.signal_Statusbar = Class_to_connect_to_QStatusBar()

        #2- Conectando os sinais criados com o painel de texto
        self.signal_Statusbar.signal_.connect(StatusBar.showMessage)

        #3- Marcando para o logger que existe um painel de texto para serem mostradas as mensagens
        self.QStatusBar_connected = True

    def exception(self, msg: str, id: 'id_msg' = None, EnviarServidorMsgs=True, ForcarEnvioServidorMsgs=False):
        """Loga uma exception com envio automático ao servidor de mensagens.

        - id: identificador do ponto de chamada. Se omitido, capturado automaticamente com frequencia=PERIOD_H1.
        - Se id.frequencia_seg < PERIOD_H1, a frequência é ignorada e substituída por PERIOD_H1 (mínima aceita);
          um warning é emitido no log e enviado ao servidor.
        - EnviarServidorMsgs: se True (padrão), envia ao servidor respeitando a frequência mínima.
        - msg pode ser uma string ou um dataframe.
        """
        if id is None:
            frame = inspect.currentframe().f_back
            id = id_msg(frequencia_seg=PERIOD_H1, line=frame.f_lineno, file=frame.f_code.co_filename)
        elif not isinstance(id, id_msg):
            raise TypeError("id must be an instance of id_msg")

        if id.frequencia_seg < PERIOD_H1:
            aviso = (f"[exception] frequencia_seg={id.frequencia_seg}s é menor que o mínimo aceitável "
                     f"({PERIOD_H1}s = 1h). Frequência será ignorada e substituída por PERIOD_H1. [{id.id()}]")
            self.logger.warning(aviso)
            if self.servidor_msgs_IsSet():
                self.servidor_msgs_SendMsg(aviso)

        freq_efetiva = max(id.frequencia_seg, PERIOD_H1)

        if self.QTextBrowser_connected:
            agora = dt.datetime.now()
            msg_com_time = ("[" + agora.strftime("%d/%m/%Y %H:%M:%S") + "]"
                            + "[EXCEPTION] " + str(msg))
            self.signal_QtextBrowser.signal_.emit(msg_com_time)
            self.signal_QtextBrowser.signal_2.emit(
                self.QTextBrowser.verticalScrollBar().maximum())

        self.logger.exception(msg)

        if EnviarServidorMsgs:
            if self.servidor_msgs_IsSet():
                key = id.id()
                agora = dt.datetime.now()
                ultimo = Class_Mensagem_Log.ultimo_envio_msg_exception_ids.get(key)
                if (ultimo is None or
                        (agora - ultimo).total_seconds() >= freq_efetiva):
                    self.servidor_msgs_SendMsg(
                        self._formatar_msg_servidor("EXCEPTION", msg, id),
                        ForcarEnvioServidorMsgs)
                    Class_Mensagem_Log.ultimo_envio_msg_exception_ids[key] = agora
            else:
                self.servidor_msgs_NotSetedMsError(False)

    def critical(self, msg, id: 'id_msg', EnviarServidorMsgs=False, ForcarEnvioServidorMsgs=False):
        """ Mostra uma mensagem de erro CRITICAL. O programa não continuará a tarefa.
        CRITICAL é um problema gerado provavelmente porque algo inesperado aconteceu.

        Indica um bug ou necessidade de melhoria no código

        - msg pode ser uma string ou um dataframe
        """
        msg = self.MsgToString(msg)
        if(self.QTextBrowser_connected):
            self.PrintMsgToQTextBrowser(msg,"CRITICAL")

        self.logger.critical(msg)

        if(EnviarServidorMsgs):
            if self.servidor_msgs_IsSet():
                self.servidor_msgs_SendMsg(self._formatar_msg_servidor("CRITICAL", msg, id), ForcarEnvioServidorMsgs)
            else:
                self.servidor_msgs_NotSetedMsError()

    def erro(self, msg, id: 'id_msg', EnviarServidorMsgs=False, ForcarEnvioServidorMsgs=False):
        """ Mostra uma mensagem de ERRO. O programa não continuará a tarefa.
        ERRO é um problema gerado devido ao mal uso do programa pelo usuário.
        Por exemplo o usuário coloca uma string vazia em um formulário que deveria ter uma string preenchida.
        Ou o usuário seleciona um arquivo .txt ao invés de um arquivo .csv, que era o necessário pelo programa.

        Indica que o usuário deve corrigir o input que ele deu ao programa

        - msg pode ser uma string ou um dataframe
        """
        msg = self.MsgToString(msg)
        if(self.QTextBrowser_connected):
            self.PrintMsgToQTextBrowser(msg,"ERRO")

        self.logger.error(msg)
        if(EnviarServidorMsgs):
            if self.servidor_msgs_IsSet():
                self.servidor_msgs_SendMsg(self._formatar_msg_servidor("ERRO", msg, id), ForcarEnvioServidorMsgs)
            else:
                self.servidor_msgs_NotSetedMsError()

    def warning(self, msg, id: 'id_msg', EnviarServidorMsgs=False, ForcarEnvioServidorMsgs=False):
        """Loga um alerta: situação não ideal, mas o processamento continua e gera resultado.

        Uso: linhas ignoradas em CSV com erros, CPFs com dígito inválido descartados etc.
        Diferente de ERRO e CRITICAL, o programa entrega um resultado (possivelmente parcial).

        - id: identificador do ponto de chamada (obrigatório).
        - EnviarServidorMsgs: se True, envia ao servidor (padrão False).
        - msg pode ser uma string ou um dataframe.
        """
        msg = self.MsgToString(msg)
        if(self.QTextBrowser_connected):
            self.PrintMsgToQTextBrowser(msg,"WARNING")

        self.logger.warning(msg)

        if(EnviarServidorMsgs):
            if self.servidor_msgs_IsSet():
                self.servidor_msgs_SendMsg(self._formatar_msg_servidor("WARNING", msg, id), ForcarEnvioServidorMsgs)
            else:
                self.servidor_msgs_NotSetedMsError()

    def info(self, msg, id: 'id_msg' = None, EnviarServidorMsgs=False, ForcarEnvioServidorMsgs=False):
        """Loga uma mensagem informativa ao usuário.

        Uso: confirmações de ações concluídas, listagem de itens processados etc.
        Diferente de WARNING, não indica nenhuma especificidade no resultado gerado.

        - id: identificador do ponto de chamada. Se omitido, capturado automaticamente com frequencia=0.
        - EnviarServidorMsgs: se True, envia ao servidor (padrão False).
        - msg pode ser uma string ou um dataframe.
        """
        if id is None:
            frame = inspect.currentframe().f_back
            id = id_msg(frequencia_seg=0, line=frame.f_lineno, file=frame.f_code.co_filename)
        msg = self.MsgToString(msg)
        if(self.QTextBrowser_connected):
            self.PrintMsgToQTextBrowser(msg,"INFO")

        self.logger.info(msg)
        if(EnviarServidorMsgs):
            if self.servidor_msgs_IsSet():
                self.servidor_msgs_SendMsg(self._formatar_msg_servidor("INFO", msg, id), ForcarEnvioServidorMsgs)
            else:
                self.servidor_msgs_NotSetedMsError()

    def debug(self, msg, id: 'id_msg' = None, EnviarServidorMsgs=False, ForcarEnvioServidorMsgs=False):
        """Loga uma mensagem de depuração, visível apenas em modo DEBUG.

        Uso: valores intermediários, versão do ambiente, inputs recebidos etc.
        Diferente de INFO, não é exibida ao usuário final fora do modo DEBUG.

        - id: identificador do ponto de chamada. Se omitido, capturado automaticamente com frequencia=0.
        - EnviarServidorMsgs: se True, envia ao servidor (padrão False).
        - msg pode ser uma string ou um dataframe.
        """
        if id is None:
            frame = inspect.currentframe().f_back
            id = id_msg(frequencia_seg=0, line=frame.f_lineno, file=frame.f_code.co_filename)
        msg = self.MsgToString(msg)
        if(self.QTextBrowser_connected and DebugModeTester.__debug_mode__):
            self.PrintMsgToQTextBrowser(msg,"DEBUG")
        self.logger.debug(msg)

        if(EnviarServidorMsgs):
            if self.servidor_msgs_IsSet():
                self.servidor_msgs_SendMsg(self._formatar_msg_servidor("DEBUG", msg, id), ForcarEnvioServidorMsgs)
            else:
                self.servidor_msgs_NotSetedMsError()

    def MsgToString(self,msg,max_linhas_tabela=10):
        ''' Padroniza a mensagem para str
        OBS: Se for um dataframe, ele será convertido para uma tabela em formato de string de até max_linhas_tabela
        '''
        mensagem_type_is_dataframe = self.TestIfMsgIsDataframe(msg)

        if (mensagem_type_is_dataframe):
            msg = msg.to_string(max_rows=max_linhas_tabela)
            msg = msg+'\n'
        elif (type(msg) != str):
            try:
                msg = str(msg)
            except Exception as erro:
                self.logger.exception(erro)
                print("Não conseguiu converter para str a mensagem de log:")
                try:
                    print("type:" + str(type(msg)))
                    print (msg)
                except Exception as erro:
                    self.logger.exception(erro)

        return msg

    def PrintMsgToQTextBrowser(self,msg_str,motivo:str="INFO"):
        ''' Mostra a mensagem no QTextBrowser de PYQT5 '''
        agora = dt.datetime.now()

        msg_com_time = "["+agora.strftime("%d/%m/%Y %H:%M:%S")+"]" +"["+motivo+"] "

        msg_com_time = msg_com_time + msg_str

        self.signal_QtextBrowser.signal_.emit(msg_com_time) #Mandando a mensagem para ser exibida
        self.signal_QtextBrowser.signal_2.emit(self.QTextBrowser.verticalScrollBar().maximum()) # Movendo o cursor do painel para o final

    @staticmethod
    def TestIfMsgIsDataframe(msg):
        ''' Verifica se a mensagem é um dataframe
         Só verifica se o móduo pandas foi importado
           '''

        mensagem_type_is_dataframe = False
        if (PANDAS_IMPORTADO and type(msg) != str):
            if (type(msg) == pd.DataFrame):
                mensagem_type_is_dataframe = True

        return mensagem_type_is_dataframe

    def setStatusbar_text(self,msg):
        ''' Se existe um QStatusBar, muda a mensagem dele, mas sem gerar log '''
        if(self.QStatusBar_connected):
            agora = dt.datetime.now()
            msg_com_time = "["+agora.strftime("%d/%m/%Y %H:%M:%S")+"] " + msg
            self.signal_Statusbar.signal_.emit(msg_com_time) #Mandando a mensagem para ser exibida

logger = Class_Mensagem_Log("Root")
