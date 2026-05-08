import os
import pytest

from my_modules.Class_Mensagem_Log import Class_Mensagem_Log, id_msg


_TELEGRAM_OK = bool(os.environ.get("TELEGRAM_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))
_PUSHBULLET_OK = bool(os.environ.get("PushBullet_APIKEY"))

pytestmark = pytest.mark.skipif(
    not (_TELEGRAM_OK or _PUSHBULLET_OK),
    reason="Nenhum servidor de mensagens configurado no .env — skip integração",
)


@pytest.fixture(autouse=True)
def reset_estado_classe():
    Class_Mensagem_Log.SERVIDOR_MSGS_ultima_msg_enviada_time = 0
    Class_Mensagem_Log.ultimo_envio_msg_exception_ids = {}
    yield
    Class_Mensagem_Log.SERVIDOR_MSGS_ultima_msg_enviada_time = 0
    Class_Mensagem_Log.ultimo_envio_msg_exception_ids = {}


class TestClassMensagemLogIntegracao:

    def test_servidor_msgs_is_set(self):
        logger = Class_Mensagem_Log("IntegracaoTeste")
        assert logger.servidor_msgs_IsSet() is True

    def test_exception_envia_msg_real(self):
        logger = Class_Mensagem_Log("IntegracaoTeste")
        msg_id = id_msg(frequencia_seg=1, line=1, file="test_integracao.py")
        logger.exception(
            "[TESTE DE INTEGRAÇÃO] Class_Mensagem_Log.exception()",
            id=msg_id,
            EnviarServidorMsgs=True,
            ForcarEnvioServidorMsgs=True,
        )
