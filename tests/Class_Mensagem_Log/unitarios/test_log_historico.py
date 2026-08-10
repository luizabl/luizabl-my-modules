"""Testes da leitura e da rotacao compactada dos logs da aplicacao."""

import datetime
import gzip
import logging
import time
from pathlib import Path

import pytest

from my_modules.log_historico import (
    HandlerArquivoDiarioCompactado,
    ler_log_aplicacao,
    obter_handler_arquivo_compartilhado,
)


@pytest.fixture
def fixture_diretorio_aplicacao(tmp_path: Path) -> Path:
    return tmp_path


# ----------------------------------------------------
# ler_log_aplicacao
# ----------------------------------------------------

def test_ler_log_aplicacao_retorna_ultimas_linhas_em_ordem_cronologica(
    fixture_diretorio_aplicacao: Path,
) -> None:
    log_path = fixture_diretorio_aplicacao / "app.log"
    log_path.write_text("linha 1\nlinha 2\nlinha 3\n", encoding="utf-8")

    resultado = ler_log_aplicacao(
        quantidade=2,
        diretorio_aplicacao=fixture_diretorio_aplicacao,
    )

    assert resultado == {
        "data": datetime.date.today().isoformat(),
        "origem": "atual",
        "quantidade_solicitada": 2,
        "quantidade_retornada": 2,
        "linhas": ["linha 2", "linha 3"],
    }


@pytest.mark.parametrize("quantidade", [0, 501])
def test_ler_log_aplicacao_rejeita_quantidade_invalida(
    fixture_diretorio_aplicacao: Path,
    quantidade: int,
) -> None:
    with pytest.raises(ValueError, match="entre 1 e 500"):
        ler_log_aplicacao(
            quantidade=quantidade,
            diretorio_aplicacao=fixture_diretorio_aplicacao,
        )


def test_ler_log_aplicacao_rejeita_data_futura(
    fixture_diretorio_aplicacao: Path,
) -> None:
    data_futura = datetime.date.today() + datetime.timedelta(days=1)

    with pytest.raises(ValueError, match="futura"):
        ler_log_aplicacao(
            quantidade=10,
            data=data_futura.isoformat(),
            diretorio_aplicacao=fixture_diretorio_aplicacao,
        )


def test_ler_log_aplicacao_informa_arquivo_atual_ausente(
    fixture_diretorio_aplicacao: Path,
) -> None:
    with pytest.raises(FileNotFoundError, match="app.log"):
        ler_log_aplicacao(
            quantidade=10,
            diretorio_aplicacao=fixture_diretorio_aplicacao,
        )


def test_ler_log_aplicacao_le_historico_gzip(
    fixture_diretorio_aplicacao: Path,
) -> None:
    data_historica = datetime.date.today() - datetime.timedelta(days=1)
    historico_dir = fixture_diretorio_aplicacao / "logs_historicos"
    historico_dir.mkdir()
    historico_path = historico_dir / f"app-{data_historica.isoformat()}.log.gz"
    with gzip.open(historico_path, "wt", encoding="utf-8") as arquivo:
        arquivo.write("historico 1\nhistorico 2\nhistorico 3\n")

    resultado = ler_log_aplicacao(
        quantidade=2,
        data=data_historica.isoformat(),
        diretorio_aplicacao=fixture_diretorio_aplicacao,
    )

    assert resultado["origem"] == "historico"
    assert resultado["linhas"] == ["historico 2", "historico 3"]


def test_ler_log_aplicacao_le_historico_pendente(
    fixture_diretorio_aplicacao: Path,
) -> None:
    data_historica = datetime.date.today() - datetime.timedelta(days=1)
    historico_dir = fixture_diretorio_aplicacao / "logs_historicos"
    historico_dir.mkdir()
    pendente_path = historico_dir / f"app-{data_historica.isoformat()}.log.pending"
    pendente_path.write_text("pendente 1\npendente 2\n", encoding="utf-8")

    resultado = ler_log_aplicacao(
        quantidade=1,
        data=data_historica.isoformat(),
        diretorio_aplicacao=fixture_diretorio_aplicacao,
    )

    assert resultado["origem"] == "historico_pendente"
    assert resultado["linhas"] == ["pendente 2"]


# ----------------------------------------------------
# HandlerArquivoDiarioCompactado
# ----------------------------------------------------

def test_handler_rotaciona_e_compacta_sem_perder_conteudo(
    fixture_diretorio_aplicacao: Path,
) -> None:
    log_path = fixture_diretorio_aplicacao / "app.log"
    data_anterior = datetime.date.today() - datetime.timedelta(days=1)
    handler = HandlerArquivoDiarioCompactado(log_path)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger(f"teste_rotacao_{time.time_ns()}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    try:
        logger.info("linha anterior")
        handler.rotacionar_para_nova_data(data_anterior, datetime.date.today())
        logger.info("linha atual")
        handler.aguardar_compactacoes(timeout=5.0)

        historico_path = (
            fixture_diretorio_aplicacao
            / "logs_historicos"
            / f"app-{data_anterior.isoformat()}.log.gz"
        )
        with gzip.open(historico_path, "rt", encoding="utf-8") as arquivo:
            assert arquivo.read().splitlines() == ["linha anterior"]
        assert log_path.read_text(encoding="utf-8").splitlines() == ["linha atual"]
    finally:
        logger.removeHandler(handler)
        handler.close()


def test_handler_recupera_compactacao_pendente(
    fixture_diretorio_aplicacao: Path,
) -> None:
    data_historica = datetime.date.today() - datetime.timedelta(days=1)
    historico_dir = fixture_diretorio_aplicacao / "logs_historicos"
    historico_dir.mkdir()
    pendente_path = historico_dir / f"app-{data_historica.isoformat()}.log.pending"
    pendente_path.write_text("recuperar\n", encoding="utf-8")

    handler = HandlerArquivoDiarioCompactado(
        fixture_diretorio_aplicacao / "app.log"
    )
    try:
        handler.aguardar_compactacoes(timeout=5.0)
        assert not pendente_path.exists()
        with gzip.open(
            historico_dir / f"app-{data_historica.isoformat()}.log.gz",
            "rt",
            encoding="utf-8",
        ) as arquivo:
            assert arquivo.read() == "recuperar\n"
    finally:
        handler.close()


# ----------------------------------------------------
# obter_handler_arquivo_compartilhado
# ----------------------------------------------------

def test_obter_handler_arquivo_compartilhado_reutiliza_mesma_instancia(
    fixture_diretorio_aplicacao: Path,
) -> None:
    log_path = fixture_diretorio_aplicacao / "app.log"

    primeiro = obter_handler_arquivo_compartilhado(log_path)
    segundo = obter_handler_arquivo_compartilhado(log_path)

    assert primeiro is segundo
