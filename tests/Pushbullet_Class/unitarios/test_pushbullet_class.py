import datetime
import logging
import os
import pytest
from unittest.mock import patch, MagicMock

from my_modules.Pushbullet_Class import Pushbullet_Class


FAKE_KEY = "o.fake_test_api_key"


@pytest.fixture(autouse=True)
def clear_env():
    """Garante que PushBullet_APIKEY não está no env durante os testes."""
    saved = os.environ.pop("PushBullet_APIKEY", None)
    yield
    if saved is not None:
        os.environ["PushBullet_APIKEY"] = saved


def make_pb(api_key=FAKE_KEY):
    """Cria instância de Pushbullet_Class com a API Pushbullet mockada."""
    mock_motor = MagicMock()
    with patch("my_modules.Pushbullet_Class.Pushbullet", return_value=mock_motor):
        pb = Pushbullet_Class()
        if api_key:
            pb.PushbulletSet(api_key)
    return pb, mock_motor


# ── PushbulletIsSet ───────────────────────────────────────────────────────────

class TestPushbulletIsSet:

    def test_false_quando_nao_configurado(self):
        with patch("my_modules.Pushbullet_Class.Pushbullet"):
            pb = Pushbullet_Class()
        assert pb.PushbulletIsSet() is False

    def test_true_apos_PushbulletSet(self):
        pb, _ = make_pb()
        assert pb.PushbulletIsSet() is True

    def test_auto_configurado_via_env_no_init(self):
        mock_motor = MagicMock()
        with patch.dict(os.environ, {"PushBullet_APIKEY": FAKE_KEY}):
            with patch("my_modules.Pushbullet_Class.Pushbullet", return_value=mock_motor):
                pb = Pushbullet_Class()
        assert pb.PushbulletIsSet() is True

    def test_lazy_configurado_via_env_no_IsSet(self):
        with patch("my_modules.Pushbullet_Class.Pushbullet"):
            pb = Pushbullet_Class()
        assert pb.PushbulletIsSet() is False

        mock_motor = MagicMock()
        with patch.dict(os.environ, {"PushBullet_APIKEY": FAKE_KEY}):
            with patch("my_modules.Pushbullet_Class.Pushbullet", return_value=mock_motor):
                result = pb.PushbulletIsSet()
        assert result is True


# ── PushbulletSet ─────────────────────────────────────────────────────────────

class TestPushbulletSet:

    def test_intervalo_zero_raises_ValueError(self):
        with patch("my_modules.Pushbullet_Class.Pushbullet"):
            pb = Pushbullet_Class()
            with pytest.raises(ValueError):
                pb.PushbulletSet(FAKE_KEY, IntervaloMinimo_seg=0)

    def test_intervalo_negativo_raises_ValueError(self):
        with patch("my_modules.Pushbullet_Class.Pushbullet"):
            pb = Pushbullet_Class()
            with pytest.raises(ValueError):
                pb.PushbulletSet(FAKE_KEY, IntervaloMinimo_seg=-5)

    def test_intervalo_1_valido(self):
        pb, _ = make_pb(api_key=None)
        with patch("my_modules.Pushbullet_Class.Pushbullet"):
            pb.PushbulletSet(FAKE_KEY, IntervaloMinimo_seg=1)
        assert pb.PushbulletIsSet() is True


# ── PushbulletSendMsg: validação de parâmetros ────────────────────────────────

class TestPushbulletSendMsgValidacao:

    def test_msg_nao_str_raises_TypeError(self):
        pb, _ = make_pb()
        with pytest.raises(TypeError):
            pb.PushbulletSendMsg("titulo", 123, motivo="exception")

    def test_motivo_none_raises_ValueError(self):
        pb, _ = make_pb()
        with pytest.raises(ValueError):
            pb.PushbulletSendMsg("titulo", "msg", motivo=None)


# ── PushbulletSendMsg: throttling ─────────────────────────────────────────────

class TestPushbulletSendMsgThrottling:

    def test_primeira_chamada_envia(self):
        pb, mock_motor = make_pb()
        pb.PushbulletSendMsg("titulo", "msg", motivo="exception")
        mock_motor.push_note.assert_called_once_with("titulo", "msg")

    def test_suprimido_dentro_do_intervalo(self):
        pb, mock_motor = make_pb()
        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 5)  # 5 s < 10 s (default)

        with patch("my_modules.Pushbullet_Class.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t0
            pb.PushbulletSendMsg("titulo", "msg", motivo="exception")

        assert mock_motor.push_note.call_count == 1

        with patch("my_modules.Pushbullet_Class.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t1
            pb.PushbulletSendMsg("titulo", "msg", motivo="exception")

        assert mock_motor.push_note.call_count == 1

    def test_envia_apos_intervalo(self):
        pb, mock_motor = make_pb()
        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 11)  # 11 s > 10 s (default)

        with patch("my_modules.Pushbullet_Class.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t0
            pb.PushbulletSendMsg("titulo", "msg", motivo="exception")

        assert mock_motor.push_note.call_count == 1

        with patch("my_modules.Pushbullet_Class.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t1
            pb.PushbulletSendMsg("titulo", "msg", motivo="exception")

        assert mock_motor.push_note.call_count == 2

    def test_ForcarEnvio_ignora_intervalo(self):
        pb, mock_motor = make_pb()
        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 1)  # 1 s < 10 s

        with patch("my_modules.Pushbullet_Class.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t0
            pb.PushbulletSendMsg("titulo", "msg", motivo="exception")

        with patch("my_modules.Pushbullet_Class.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t1
            pb.PushbulletSendMsg("titulo", "msg", motivo="exception", ForcarEnvio=True)

        assert mock_motor.push_note.call_count == 2

    def test_motivos_diferentes_tem_controle_independente(self):
        pb, mock_motor = make_pb()
        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 5)  # dentro do intervalo de "exception"

        with patch("my_modules.Pushbullet_Class.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t0
            pb.PushbulletSendMsg("titulo", "msg", motivo="exception")

        with patch("my_modules.Pushbullet_Class.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t1
            pb.PushbulletSendMsg("titulo", "msg", motivo="info")  # motivo diferente

        assert mock_motor.push_note.call_count == 2


# ── PushbulletSendMsg: não configurado ────────────────────────────────────────

class TestPushbulletSendMsgNaoConfigurado:

    def test_logs_critical_apenas_uma_vez(self, caplog):
        with patch("my_modules.Pushbullet_Class.Pushbullet"):
            pb = Pushbullet_Class()
        with caplog.at_level(logging.CRITICAL, logger="my_modules.Pushbullet_Class"):
            pb.PushbulletSendMsg("titulo", "msg", motivo="exception")
            pb.PushbulletSendMsg("titulo", "msg", motivo="exception")
        assert len(caplog.records) == 1
