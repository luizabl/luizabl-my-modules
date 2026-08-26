"""Testes unitarios para healthcheck_ping.py."""

from unittest.mock import Mock, patch
from urllib.error import URLError
from pathlib import Path

import pytest

from my_modules.healthcheck_ping import Healthcheck_ping, PING_TIMEOUT_SECONDS


# ----------------------------------------------------
# Healthcheck_ping
# ----------------------------------------------------


def test_ping_usa_configuracao_do_ambiente_na_primeira_tentativa(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEALTHCHECK_URL", "http://healthcheck.test:8000/")
    monkeypatch.setenv("HEALTHCHECK_TOKEN", "token de teste")
    response = Mock()
    response.read.return_value = b"OK"

    with patch(
        "my_modules.healthcheck_ping.urlopen",
        return_value=response,
    ) as mock_urlopen:
        assert Healthcheck_ping("Servico teste") == "OK"

    request = mock_urlopen.call_args.args[0]
    assert request.full_url == "http://healthcheck.test:8000/ping/Servico%20teste"
    assert request.get_header("X-healthcheck-token") == "token de teste"
    assert mock_urlopen.call_args.kwargs["timeout"] == PING_TIMEOUT_SECONDS
    assert mock_urlopen.call_count == 1


def test_ping_repete_uma_vez_apos_erro_e_sucesso_na_segunda_tentativa(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEALTHCHECK_URL", "http://healthcheck.test:8000/")
    monkeypatch.setenv("HEALTHCHECK_TOKEN", "token de teste")
    response = Mock()
    response.read.return_value = b"OK"

    with patch(
        "my_modules.healthcheck_ping.urlopen",
        side_effect=[URLError("timed out"), response],
    ) as mock_urlopen:
        assert Healthcheck_ping("Servico teste") == "OK"

    assert mock_urlopen.call_count == 2
    assert all(
        call.kwargs["timeout"] == PING_TIMEOUT_SECONDS
        for call in mock_urlopen.call_args_list
    )


def test_ping_repete_uma_vez_apos_resposta_de_erro(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEALTHCHECK_URL", "http://healthcheck.test:8000/")
    monkeypatch.setenv("HEALTHCHECK_TOKEN", "token de teste")
    error_response = Mock()
    error_response.read.return_value = b"ERROR_SERVICE_NOT_REGISTERED"
    success_response = Mock()
    success_response.read.return_value = b"OK"

    with patch(
        "my_modules.healthcheck_ping.urlopen",
        side_effect=[error_response, success_response],
    ) as mock_urlopen:
        assert Healthcheck_ping("Servico teste") == "OK"

    assert mock_urlopen.call_count == 2


def test_ping_retorna_os_dois_erros_quando_ambas_tentativas_falham(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEALTHCHECK_URL", "http://healthcheck.test:8000/")
    monkeypatch.setenv("HEALTHCHECK_TOKEN", "token de teste")

    with patch(
        "my_modules.healthcheck_ping.urlopen",
        side_effect=[URLError("primeiro timeout"), URLError("segundo timeout")],
    ) as mock_urlopen:
        result = Healthcheck_ping("Servico teste")

    assert mock_urlopen.call_count == 2
    assert "Falha no healthcheck apos 2 tentativas" in result
    assert "primeiro timeout" in result
    assert "segundo timeout" in result


def test_ping_retorna_erro_quando_configuracao_esta_ausente(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HEALTHCHECK_URL", raising=False)
    monkeypatch.delenv("HEALTHCHECK_TOKEN", raising=False)

    assert "HEALTHCHECK_URL e HEALTHCHECK_TOKEN" in Healthcheck_ping("Servico teste")


def test_ping_carrega_configuracao_do_arquivo_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / ".env").write_text(
        "HEALTHCHECK_URL=http://healthcheck.test:8000\nHEALTHCHECK_TOKEN=token-de-teste\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HEALTHCHECK_URL", raising=False)
    monkeypatch.delenv("HEALTHCHECK_TOKEN", raising=False)
    response = Mock()
    response.read.return_value = b"OK"

    with patch(
        "my_modules.healthcheck_ping.urlopen",
        return_value=response,
    ) as mock_urlopen:
        assert Healthcheck_ping("Servico") == "OK"

    request = mock_urlopen.call_args.args[0]
    assert "token=" not in request.full_url
    assert request.get_header("X-healthcheck-token") == "token-de-teste"
