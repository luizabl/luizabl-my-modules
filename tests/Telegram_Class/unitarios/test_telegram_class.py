import datetime
import logging
import os
import pytest
from unittest.mock import patch, MagicMock
from urllib.parse import parse_qs

from my_modules.Telegram_Class import Telegram_Class


FAKE_TOKEN   = "1234567890:faketoken"
FAKE_CHAT_ID = "987654321"


@pytest.fixture(autouse=True)
def clear_env():
    """Garante que TELEGRAM_TOKEN e TELEGRAM_CHAT_ID não estão no env durante os testes."""
    saved_token   = os.environ.pop("TELEGRAM_TOKEN", None)
    saved_chat_id = os.environ.pop("TELEGRAM_CHAT_ID", None)
    yield
    if saved_token   is not None: os.environ["TELEGRAM_TOKEN"]   = saved_token
    if saved_chat_id is not None: os.environ["TELEGRAM_CHAT_ID"] = saved_chat_id


def make_tg(token=FAKE_TOKEN, chat_id=FAKE_CHAT_ID):
    """Cria instância de Telegram_Class sem depender de env vars."""
    tg = Telegram_Class()
    if token and chat_id:
        tg.TelegramSet(token, chat_id)
    return tg


# ── TelegramIsSet ─────────────────────────────────────────────────────────────

class TestTelegramIsSet:

    def test_false_quando_nao_configurado(self):
        tg = Telegram_Class()
        assert tg.TelegramIsSet() is False

    def test_true_apos_TelegramSet(self):
        tg = make_tg()
        assert tg.TelegramIsSet() is True

    def test_auto_configurado_via_env_no_init(self):
        with patch.dict(os.environ, {"TELEGRAM_TOKEN": FAKE_TOKEN, "TELEGRAM_CHAT_ID": FAKE_CHAT_ID}):
            tg = Telegram_Class()
        assert tg.TelegramIsSet() is True

    def test_lazy_configurado_via_env_no_IsSet(self):
        tg = Telegram_Class()
        assert tg.TelegramIsSet() is False

        with patch.dict(os.environ, {"TELEGRAM_TOKEN": FAKE_TOKEN, "TELEGRAM_CHAT_ID": FAKE_CHAT_ID}):
            result = tg.TelegramIsSet()
        assert result is True


# ── TelegramSet ───────────────────────────────────────────────────────────────

class TestTelegramSet:

    def test_intervalo_zero_raises_ValueError(self):
        tg = Telegram_Class()
        with pytest.raises(ValueError):
            tg.TelegramSet(FAKE_TOKEN, FAKE_CHAT_ID, IntervaloMinimo_seg=0)

    def test_intervalo_negativo_raises_ValueError(self):
        tg = Telegram_Class()
        with pytest.raises(ValueError):
            tg.TelegramSet(FAKE_TOKEN, FAKE_CHAT_ID, IntervaloMinimo_seg=-5)

    def test_intervalo_1_valido(self):
        tg = Telegram_Class()
        tg.TelegramSet(FAKE_TOKEN, FAKE_CHAT_ID, IntervaloMinimo_seg=1)
        assert tg.TelegramIsSet() is True


# ── TelegramSendMsg: validação de parâmetros ──────────────────────────────────

class TestTelegramSendMsgValidacao:

    def test_msg_nao_str_raises_TypeError(self):
        tg = make_tg()
        with patch("my_modules.Telegram_Class.urlopen"):
            with pytest.raises(TypeError):
                tg.TelegramSendMsg("titulo", 123, motivo="exception")

    def test_motivo_none_raises_ValueError(self):
        tg = make_tg()
        with patch("my_modules.Telegram_Class.urlopen"):
            with pytest.raises(ValueError):
                tg.TelegramSendMsg("titulo", "msg", motivo=None)


# ── TelegramSendMsg: throttling ───────────────────────────────────────────────

class TestTelegramSendMsgThrottling:

    def test_primeira_chamada_envia(self):
        tg = make_tg()
        with patch("my_modules.Telegram_Class.urlopen") as mock_urlopen:
            tg.TelegramSendMsg("titulo", "msg", motivo="exception")
        mock_urlopen.assert_called_once()

    def test_suprimido_dentro_do_intervalo(self):
        tg = make_tg()
        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 5)  # 5 s < 10 s (default)

        with patch("my_modules.Telegram_Class.urlopen") as mock_urlopen:
            with patch("my_modules.Telegram_Class.dt") as mock_dt:
                mock_dt.datetime.now.return_value = t0
                tg.TelegramSendMsg("titulo", "msg", motivo="exception")

            assert mock_urlopen.call_count == 1

            with patch("my_modules.Telegram_Class.dt") as mock_dt:
                mock_dt.datetime.now.return_value = t1
                tg.TelegramSendMsg("titulo", "msg", motivo="exception")

            assert mock_urlopen.call_count == 1

    def test_envia_apos_intervalo(self):
        tg = make_tg()
        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 11)  # 11 s > 10 s (default)

        with patch("my_modules.Telegram_Class.urlopen") as mock_urlopen:
            with patch("my_modules.Telegram_Class.dt") as mock_dt:
                mock_dt.datetime.now.return_value = t0
                tg.TelegramSendMsg("titulo", "msg", motivo="exception")

            assert mock_urlopen.call_count == 1

            with patch("my_modules.Telegram_Class.dt") as mock_dt:
                mock_dt.datetime.now.return_value = t1
                tg.TelegramSendMsg("titulo", "msg", motivo="exception")

            assert mock_urlopen.call_count == 2

    def test_ForcarEnvio_ignora_intervalo(self):
        tg = make_tg()
        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 1)  # 1 s < 10 s

        with patch("my_modules.Telegram_Class.urlopen") as mock_urlopen:
            with patch("my_modules.Telegram_Class.dt") as mock_dt:
                mock_dt.datetime.now.return_value = t0
                tg.TelegramSendMsg("titulo", "msg", motivo="exception")

            with patch("my_modules.Telegram_Class.dt") as mock_dt:
                mock_dt.datetime.now.return_value = t1
                tg.TelegramSendMsg("titulo", "msg", motivo="exception", ForcarEnvio=True)

            assert mock_urlopen.call_count == 2

    def test_motivos_diferentes_tem_controle_independente(self):
        tg = make_tg()
        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 5)  # dentro do intervalo de "exception"

        with patch("my_modules.Telegram_Class.urlopen") as mock_urlopen:
            with patch("my_modules.Telegram_Class.dt") as mock_dt:
                mock_dt.datetime.now.return_value = t0
                tg.TelegramSendMsg("titulo", "msg", motivo="exception")

            with patch("my_modules.Telegram_Class.dt") as mock_dt:
                mock_dt.datetime.now.return_value = t1
                tg.TelegramSendMsg("titulo", "msg", motivo="info")  # motivo diferente

            assert mock_urlopen.call_count == 2


# ── TelegramSendMsg: não configurado ─────────────────────────────────────────

class TestTelegramSendMsgNaoConfigurado:

    def test_logs_critical_apenas_uma_vez(self, caplog):
        tg = Telegram_Class()
        with caplog.at_level(logging.CRITICAL, logger="my_modules.Telegram_Class"):
            tg.TelegramSendMsg("titulo", "msg", motivo="exception")
            tg.TelegramSendMsg("titulo", "msg", motivo="exception")
        assert len(caplog.records) == 1


# ── TelegramSendMsg: formato da requisição ────────────────────────────────────

class TestTelegramSendMsgFormato:

    def test_url_contem_token_e_endpoint(self):
        tg = make_tg()
        with patch("my_modules.Telegram_Class.urlopen") as mock_urlopen:
            tg.TelegramSendMsg("titulo", "msg", motivo="exception")
        url = mock_urlopen.call_args[0][0]
        assert f"bot{FAKE_TOKEN}/sendMessage" in url

    def test_payload_contem_chat_id_e_texto(self):
        tg = make_tg()
        with patch("my_modules.Telegram_Class.urlopen") as mock_urlopen:
            tg.TelegramSendMsg("Titulo", "mensagem", motivo="exception")
        data_bytes = mock_urlopen.call_args[1]["data"]
        payload = parse_qs(data_bytes.decode())
        assert payload["chat_id"] == [FAKE_CHAT_ID]
        assert "Titulo" in payload["text"][0]
        assert "mensagem" in payload["text"][0]

    def test_timeout_de_5_segundos(self):
        tg = make_tg()
        with patch("my_modules.Telegram_Class.urlopen") as mock_urlopen:
            tg.TelegramSendMsg("titulo", "msg", motivo="exception")
        assert mock_urlopen.call_args[1]["timeout"] == 5
