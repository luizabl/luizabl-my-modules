import os
import pytest

from my_modules.Telegram_Class import Telegram_Class


pytestmark = pytest.mark.skipif(
    not (os.environ.get("TELEGRAM_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")),
    reason="TELEGRAM_TOKEN e TELEGRAM_CHAT_ID não definidos no .env — skip integração",
)


class TestTelegramIntegracao:

    def test_is_set_com_env_vars(self):
        tg = Telegram_Class()
        assert tg.TelegramIsSet() is True

    def test_envio_mensagem_real(self):
        tg = Telegram_Class()
        tg.TelegramSet(
            os.environ["TELEGRAM_TOKEN"],
            os.environ["TELEGRAM_CHAT_ID"],
            IntervaloMinimo_seg=1,
        )
        tg.TelegramSendMsg("[TESTE DE INTEGRAÇÃO] Telegram_Class.TelegramSendMsg", ForcarEnvio=True)
