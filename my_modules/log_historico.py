"""Leitura eficiente e rotacao diaria compactada do log da aplicacao."""

from __future__ import annotations

import datetime
import gzip
import logging
import os
import shutil
import threading
import time
import weakref
from collections import deque
from pathlib import Path


MAX_LINHAS_LOG = 500
NOME_LOG_ATUAL = "app.log"
NOME_DIRETORIO_HISTORICO = "logs_historicos"
_TAMANHO_BLOCO_LEITURA = 64 * 1024


def _diretorio_aplicacao_padrao() -> Path:
    from . import DebugModeTester

    return Path(DebugModeTester.application_path)


def _validar_quantidade(quantidade: int) -> None:
    if not isinstance(quantidade, int) or isinstance(quantidade, bool):
        raise TypeError("quantidade deve ser um numero inteiro")
    if not 1 <= quantidade <= MAX_LINHAS_LOG:
        raise ValueError(f"quantidade deve estar entre 1 e {MAX_LINHAS_LOG}")


def _validar_data(data: str | None) -> datetime.date:
    if data is None:
        return datetime.date.today()
    try:
        data_consulta = datetime.date.fromisoformat(data)
    except (TypeError, ValueError) as exc:
        raise ValueError("data deve estar no formato YYYY-MM-DD") from exc
    if data_consulta > datetime.date.today():
        raise ValueError("data nao pode ser futura")
    return data_consulta


def _ler_ultimas_linhas_texto(caminho: Path, quantidade: int) -> list[str]:
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo de log nao encontrado: {caminho}")

    with caminho.open("rb") as arquivo:
        arquivo.seek(0, os.SEEK_END)
        posicao = arquivo.tell()
        conteudo = b""
        while posicao > 0 and conteudo.count(b"\n") <= quantidade:
            tamanho = min(_TAMANHO_BLOCO_LEITURA, posicao)
            posicao -= tamanho
            arquivo.seek(posicao)
            conteudo = arquivo.read(tamanho) + conteudo

    return conteudo.decode("utf-8", errors="replace").splitlines()[-quantidade:]


def _iterar_linhas_historico(caminho: Path):
    if caminho.suffix == ".gz":
        with gzip.open(caminho, "rt", encoding="utf-8", errors="replace") as arquivo:
            yield from arquivo
        return
    with caminho.open("rt", encoding="utf-8", errors="replace") as arquivo:
        yield from arquivo


def _listar_arquivos_historicos(
    diretorio_aplicacao: Path,
    data_consulta: datetime.date,
) -> list[Path]:
    diretorio = diretorio_aplicacao / NOME_DIRETORIO_HISTORICO
    prefixo = f"app-{data_consulta.isoformat()}"
    arquivos = [
        caminho
        for caminho in diretorio.glob(f"{prefixo}*")
        if caminho.name.endswith((".log.gz", ".log.pending"))
    ]
    return sorted(arquivos, key=lambda caminho: caminho.name)


def ler_log_aplicacao(
    quantidade: int = 50,
    data: str | None = None,
    diretorio_aplicacao: str | Path | None = None,
) -> dict[str, object]:
    """Retorna as ultimas linhas do log atual ou de um historico diario."""
    _validar_quantidade(quantidade)
    data_consulta = _validar_data(data)
    diretorio = (
        Path(diretorio_aplicacao)
        if diretorio_aplicacao is not None
        else _diretorio_aplicacao_padrao()
    )

    if data_consulta == datetime.date.today():
        linhas = _ler_ultimas_linhas_texto(diretorio / NOME_LOG_ATUAL, quantidade)
        origem = "atual"
    else:
        arquivos = _listar_arquivos_historicos(diretorio, data_consulta)
        if not arquivos:
            raise FileNotFoundError(
                f"Log historico nao encontrado para {data_consulta.isoformat()}"
            )
        ultimas_linhas: deque[str] = deque(maxlen=quantidade)
        for caminho in arquivos:
            for linha in _iterar_linhas_historico(caminho):
                ultimas_linhas.append(linha.rstrip("\r\n"))
        linhas = list(ultimas_linhas)
        origem = (
            "historico_pendente"
            if any(caminho.name.endswith(".pending") for caminho in arquivos)
            else "historico"
        )

    return {
        "data": data_consulta.isoformat(),
        "origem": origem,
        "quantidade_solicitada": quantidade,
        "quantidade_retornada": len(linhas),
        "linhas": linhas,
    }


class _CoordenadorRotacao:
    def __init__(self) -> None:
        self._handlers: weakref.WeakSet[HandlerArquivoDiarioCompactado] = weakref.WeakSet()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def registrar(self, handler: HandlerArquivoDiarioCompactado) -> None:
        with self._lock:
            self._handlers.add(handler)
            if self._thread is not None and self._thread.is_alive():
                return
            self._thread = threading.Thread(
                target=self._executar,
                name="RotacaoDiariaLogs",
                daemon=True,
            )
            self._thread.start()

    def remover(self, handler: HandlerArquivoDiarioCompactado) -> None:
        with self._lock:
            self._handlers.discard(handler)

    def _executar(self) -> None:
        while True:
            with self._lock:
                handlers = list(self._handlers)
            if not handlers:
                return
            data_atual = datetime.date.today()
            for handler in handlers:
                handler.rotacionar_se_necessario(data_atual)
            time.sleep(1.0)


_coordenador_rotacao = _CoordenadorRotacao()


class HandlerArquivoDiarioCompactado(logging.FileHandler):
    """FileHandler com rollover diario e compactacao Gzip em segundo plano."""

    def __init__(self, caminho_log: str | Path) -> None:
        caminho = Path(caminho_log).resolve()
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self._diretorio_historico = caminho.parent / NOME_DIRETORIO_HISTORICO
        self._diretorio_historico.mkdir(parents=True, exist_ok=True)
        self._data_log = self._obter_data_inicial(caminho)
        self._compactacoes: list[threading.Thread] = []
        self._compactacoes_lock = threading.Lock()
        super().__init__(caminho, mode="a", encoding="utf-8")
        self._recuperar_compactacoes_pendentes()
        _coordenador_rotacao.registrar(self)

    @staticmethod
    def _obter_data_inicial(caminho: Path) -> datetime.date:
        if caminho.is_file() and caminho.stat().st_size > 0:
            return datetime.datetime.fromtimestamp(caminho.stat().st_mtime).date()
        return datetime.date.today()

    def emit(self, record: logging.LogRecord) -> None:
        self.rotacionar_se_necessario(datetime.date.today())
        super().emit(record)

    def rotacionar_se_necessario(self, data_atual: datetime.date) -> None:
        if data_atual == self._data_log:
            return
        self.rotacionar_para_nova_data(self._data_log, data_atual)

    def rotacionar_para_nova_data(
        self,
        data_arquivo: datetime.date,
        data_nova: datetime.date,
    ) -> None:
        if data_nova <= data_arquivo:
            raise ValueError("data_nova deve ser posterior a data_arquivo")

        self.acquire()
        try:
            if self.stream is not None:
                self.stream.flush()
                self.stream.close()
                self.stream = None
            caminho_atual = Path(self.baseFilename)
            if caminho_atual.is_file() and caminho_atual.stat().st_size > 0:
                pendente = self._proximo_caminho_pendente(data_arquivo)
                os.replace(caminho_atual, pendente)
                self._iniciar_compactacao(pendente)
            self._data_log = data_nova
            self.stream = self._open()
        finally:
            self.release()

    def _proximo_caminho_pendente(self, data_arquivo: datetime.date) -> Path:
        data_texto = data_arquivo.isoformat()
        for indice in range(1000):
            sufixo = "" if indice == 0 else f"-{indice:03d}"
            base = self._diretorio_historico / f"app-{data_texto}{sufixo}.log"
            pendente = base.with_suffix(".log.pending")
            compactado = base.with_suffix(".log.gz")
            if not pendente.exists() and not compactado.exists():
                return pendente
        raise RuntimeError(f"Nao foi possivel nomear o historico de {data_texto}")

    def _recuperar_compactacoes_pendentes(self) -> None:
        for pendente in sorted(self._diretorio_historico.glob("*.log.pending")):
            self._iniciar_compactacao(pendente)

    def _iniciar_compactacao(self, pendente: Path) -> None:
        thread = threading.Thread(
            target=self._compactar_pendente,
            args=(pendente,),
            name=f"CompactarLog-{pendente.stem}",
            daemon=True,
        )
        with self._compactacoes_lock:
            self._compactacoes.append(thread)
        thread.start()

    @staticmethod
    def _compactar_pendente(pendente: Path) -> None:
        compactado = Path(str(pendente).removesuffix(".pending") + ".gz")
        temporario = Path(str(compactado) + ".tmp")
        try:
            with pendente.open("rb") as origem, gzip.open(
                temporario,
                "wb",
                compresslevel=6,
            ) as destino:
                shutil.copyfileobj(origem, destino, length=1024 * 1024)
            os.replace(temporario, compactado)
            pendente.unlink()
        finally:
            if temporario.exists():
                temporario.unlink()

    def aguardar_compactacoes(self, timeout: float | None = None) -> None:
        inicio = time.monotonic()
        with self._compactacoes_lock:
            threads = list(self._compactacoes)
        for thread in threads:
            restante = None
            if timeout is not None:
                restante = max(0.0, timeout - (time.monotonic() - inicio))
            thread.join(restante)
        if any(thread.is_alive() for thread in threads):
            raise TimeoutError("Compactacao do log nao terminou no prazo")

    def close(self) -> None:
        _coordenador_rotacao.remover(self)
        super().close()


_handlers_compartilhados: dict[str, HandlerArquivoDiarioCompactado] = {}
_handlers_compartilhados_lock = threading.Lock()


def obter_handler_arquivo_compartilhado(
    caminho_log: str | Path,
) -> HandlerArquivoDiarioCompactado:
    caminho = str(Path(caminho_log).resolve())
    with _handlers_compartilhados_lock:
        handler = _handlers_compartilhados.get(caminho)
        if handler is None or getattr(handler, "_closed", False):
            handler = HandlerArquivoDiarioCompactado(caminho)
            _handlers_compartilhados[caminho] = handler
        return handler
