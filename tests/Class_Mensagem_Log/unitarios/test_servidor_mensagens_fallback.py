"""Testes do diagnostico de configuracao e fallback dos servidores de mensagens."""

from typing import Tuple
from unittest.mock import MagicMock, call, patch

import pytest

import my_modules.Class_Mensagem_Log as class_mensagem_log_modulo
from my_modules.Class_Mensagem_Log import Class_Mensagem_Log


@pytest.fixture(autouse=True)
def fixture_resetar_estado_servidor_mensagens() -> None:
    """Isola os avisos emitidos uma vez por processo entre os testes."""
    Class_Mensagem_Log.SERVIDOR_MSGS_ultima_msg_enviada_time = 0
    Class_Mensagem_Log._avisos_configuracao_telegram_emitidos = set()
    Class_Mensagem_Log._aviso_fallback_telegram_emitido = False
    yield
    Class_Mensagem_Log.SERVIDOR_MSGS_ultima_msg_enviada_time = 0
    Class_Mensagem_Log._avisos_configuracao_telegram_emitidos = set()
    Class_Mensagem_Log._aviso_fallback_telegram_emitido = False


def _criar_logger_com_servidores_mockados(
    monkeypatch: pytest.MonkeyPatch,
) -> Tuple[Class_Mensagem_Log, MagicMock, MagicMock]:
    """Cria logger com Telegram e Pushbullet isolados de chamadas externas."""
    mock_telegram = MagicMock()
    mock_pushbullet = MagicMock()
    mock_pushbullet.PushbulletIsSet.return_value = True
    monkeypatch.setattr(class_mensagem_log_modulo, "TELEGRAM_IMPORTADO", True)
    monkeypatch.setattr(class_mensagem_log_modulo, "PUSHBULLET_IMPORTADO", True)
    monkeypatch.setattr(
        Class_Mensagem_Log,
        "_Class_Mensagem_Log__servidor_msgs_telegram",
        mock_telegram,
    )
    monkeypatch.setattr(
        Class_Mensagem_Log,
        "_Class_Mensagem_Log__servidor_msgs_pushbullet",
        mock_pushbullet,
    )
    return Class_Mensagem_Log("teste_servidor_mensagens_fallback"), mock_telegram, mock_pushbullet


# ----------------------------------------------------
# servidor_msgs_SendMsg
# ----------------------------------------------------
def test_credencial_parcial_do_telegram_avisa_uma_vez_e_mantem_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_TOKEN", "token-configurado")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    logger, mock_telegram, mock_pushbullet = _criar_logger_com_servidores_mockados(monkeypatch)

    with patch.object(logger.logger, "warning") as mock_warning:
        logger.servidor_msgs_SendMsg("mensagem principal")
        Class_Mensagem_Log.SERVIDOR_MSGS_ultima_msg_enviada_time = 0
        logger.servidor_msgs_SendMsg("mensagem seguinte")

    mock_telegram.TelegramSendMsg.assert_not_called()
    assert mock_pushbullet.PushbulletSendMsg.call_args_list == [
        call("mensagem principal", False),
        call("O TELEGRAM_CHAT_ID para o envio ao Telegram não está presente no env!", True),
        call("mensagem seguinte", False),
    ]
    mock_warning.assert_called_once_with(
        "O TELEGRAM_CHAT_ID para o envio ao Telegram não está presente no env!"
    )


def test_falha_do_telegram_avisa_uma_vez_e_reenvia_mensagem_original_no_pushbullet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_TOKEN", "token-configurado")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat-configurado")
    logger, mock_telegram, mock_pushbullet = _criar_logger_com_servidores_mockados(monkeypatch)
    mock_telegram.TelegramIsSet.return_value = True
    mock_telegram.TelegramSendMsg.side_effect = RuntimeError("timeout Telegram")

    with patch.object(logger.logger, "error") as mock_error:
        logger.servidor_msgs_SendMsg("mensagem principal")
        Class_Mensagem_Log.SERVIDOR_MSGS_ultima_msg_enviada_time = 0
        logger.servidor_msgs_SendMsg("mensagem seguinte")

    assert mock_pushbullet.PushbulletSendMsg.call_args_list == [
        call("mensagem principal", True),
        call("Erro no envio ao Telegram: timeout Telegram. Foi feito fallback para o Pushbullet.", True),
        call("mensagem seguinte", True),
    ]
    mock_error.assert_called_once_with(
        "Erro no envio ao Telegram: timeout Telegram. Foi feito fallback para o Pushbullet."
    )
