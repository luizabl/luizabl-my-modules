import os

import pytest

from my_modules.Class_Mensagem_Log import Class_Mensagem_Log


@pytest.fixture(autouse=True)
def reset_estado_classe():
    Class_Mensagem_Log.SERVIDOR_MSGS_ultima_msg_enviada_time = 0
    Class_Mensagem_Log.ultimo_envio_msg_exception_ids = {}
    yield
    Class_Mensagem_Log.SERVIDOR_MSGS_ultima_msg_enviada_time = 0
    Class_Mensagem_Log.ultimo_envio_msg_exception_ids = {}


@pytest.mark.skipif(
    os.environ.get("RUN_REAL_MESSAGE_TESTS") != "1",
    reason="Defina RUN_REAL_MESSAGE_TESTS=1 para executar os envios reais ao Telegram e Pushbullet.",
)
class TestClassMensagemLogIntegracao:

    def test_telegram_envia_msg_real(self):
        logger = Class_Mensagem_Log("IntegracaoTeste")
        telegram = logger._Class_Mensagem_Log__servidor_msgs_telegram
        assert telegram is not None, "Módulo Telegram não está disponível"
        assert telegram.TelegramIsSet(), "TELEGRAM_TOKEN e TELEGRAM_CHAT_ID devem estar configurados no .env"
        telegram.TelegramSendMsg(
            "[Teste de pytest no módulo Class_Mensagem_Log] Telegram",
            ForcarEnvio=True,
        )

    def test_pushbullet_envia_msg_real(self):
        logger = Class_Mensagem_Log("IntegracaoTeste")
        pushbullet = logger._Class_Mensagem_Log__servidor_msgs_pushbullet
        assert pushbullet is not None, "Módulo Pushbullet não está disponível"
        assert pushbullet.PushbulletIsSet(), "PushBullet_APIKEY deve estar configurada no .env"
        pushbullet.PushbulletSendMsg(
            "[Teste de pytest no módulo Class_Mensagem_Log] Pushbullet",
            ForcarEnvio=True,
        )
