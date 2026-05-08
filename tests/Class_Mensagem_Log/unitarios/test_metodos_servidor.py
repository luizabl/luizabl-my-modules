import uuid
import pytest
from unittest.mock import patch

from my_modules.Class_Mensagem_Log import Class_Mensagem_Log, id_msg


def make_logger():
    return Class_Mensagem_Log(str(uuid.uuid4()))


def make_id(n=1):
    return id_msg(frequencia_seg=300, line=n, file="f.py")


# ── Helpers de asserção ───────────────────────────────────────────────────────

def assert_msg_enviada(mock_send, titulo: str, msg: str, id_obj: id_msg):
    mock_send.assert_called_once()
    texto = mock_send.call_args[0][0]
    assert f"[{titulo}]" in texto
    assert msg in texto
    assert f"[{id_obj.id()}]" in texto


# ── info ──────────────────────────────────────────────────────────────────────

class TestInfoServidorMsgs:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_envia_quando_habilitado(self, _, mock_send):
        logger = make_logger()
        msg_id = make_id(1)
        logger.info("msg info", id=msg_id, EnviarServidorMsgs=True)
        assert_msg_enviada(mock_send, "INFO", "msg info", msg_id)

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_nao_envia_quando_desabilitado(self, _, mock_send):
        logger = make_logger()
        logger.info("msg info", id=make_id(2), EnviarServidorMsgs=False)
        mock_send.assert_not_called()


# ── warning ───────────────────────────────────────────────────────────────────

class TestWarningServidorMsgs:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_envia_quando_habilitado(self, _, mock_send):
        logger = make_logger()
        msg_id = make_id(3)
        logger.warning("msg warning", id=msg_id, EnviarServidorMsgs=True)
        assert_msg_enviada(mock_send, "WARNING", "msg warning", msg_id)

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_nao_envia_quando_desabilitado(self, _, mock_send):
        logger = make_logger()
        logger.warning("msg warning", id=make_id(4), EnviarServidorMsgs=False)
        mock_send.assert_not_called()


# ── erro ──────────────────────────────────────────────────────────────────────

class TestErroServidorMsgs:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_envia_quando_habilitado(self, _, mock_send):
        logger = make_logger()
        msg_id = make_id(5)
        logger.erro("msg erro", id=msg_id, EnviarServidorMsgs=True)
        assert_msg_enviada(mock_send, "ERRO", "msg erro", msg_id)

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_nao_envia_quando_desabilitado(self, _, mock_send):
        logger = make_logger()
        logger.erro("msg erro", id=make_id(6), EnviarServidorMsgs=False)
        mock_send.assert_not_called()


# ── critical ──────────────────────────────────────────────────────────────────

class TestCriticalServidorMsgs:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_envia_quando_habilitado(self, _, mock_send):
        logger = make_logger()
        msg_id = make_id(7)
        logger.critical("msg critical", id=msg_id, EnviarServidorMsgs=True)
        assert_msg_enviada(mock_send, "CRITICAL", "msg critical", msg_id)

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_nao_envia_quando_desabilitado(self, _, mock_send):
        logger = make_logger()
        logger.critical("msg critical", id=make_id(8), EnviarServidorMsgs=False)
        mock_send.assert_not_called()


# ── debug ─────────────────────────────────────────────────────────────────────

class TestDebugServidorMsgs:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_envia_quando_habilitado(self, _, mock_send):
        logger = make_logger()
        msg_id = make_id(9)
        logger.debug("msg debug", id=msg_id, EnviarServidorMsgs=True)
        assert_msg_enviada(mock_send, "DEBUG", "msg debug", msg_id)

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_nao_envia_quando_desabilitado(self, _, mock_send):
        logger = make_logger()
        logger.debug("msg debug", id=make_id(10), EnviarServidorMsgs=False)
        mock_send.assert_not_called()
