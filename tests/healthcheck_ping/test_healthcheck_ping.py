from unittest.mock import Mock, patch

from my_modules.healthcheck_ping import Healthcheck_ping


def test_ping_uses_environment_configuration(monkeypatch):
    monkeypatch.setenv("HEALTHCHECK_URL", "http://healthcheck.test:8000/")
    monkeypatch.setenv("HEALTHCHECK_TOKEN", "token de teste")
    response = Mock()
    response.read.return_value = b"OK"

    with patch("my_modules.healthcheck_ping.urlopen", return_value=response) as urlopen:
        assert Healthcheck_ping("Servico teste") == "OK"

    request = urlopen.call_args.args[0]
    assert request.full_url == (
        "http://healthcheck.test:8000/ping/Servico%20teste?token=token%20de%20teste"
    )
    assert urlopen.call_args.kwargs["timeout"] == 5


def test_ping_reports_missing_environment_configuration(monkeypatch):
    monkeypatch.delenv("HEALTHCHECK_URL", raising=False)
    monkeypatch.delenv("HEALTHCHECK_TOKEN", raising=False)

    assert "HEALTHCHECK_URL e HEALTHCHECK_TOKEN" in Healthcheck_ping("Servico teste")


def test_ping_loads_configuration_from_dotenv(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text(
        "HEALTHCHECK_URL=http://healthcheck.test:8000\nHEALTHCHECK_TOKEN=token-de-teste\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HEALTHCHECK_URL", raising=False)
    monkeypatch.delenv("HEALTHCHECK_TOKEN", raising=False)
    response = Mock()
    response.read.return_value = b"OK"

    with patch("my_modules.healthcheck_ping.urlopen", return_value=response) as urlopen:
        assert Healthcheck_ping("Servico") == "OK"

    assert "token=token-de-teste" in urlopen.call_args.args[0].full_url
