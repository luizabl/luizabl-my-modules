import uuid
import inspect
import os
import datetime
import pytest
from unittest.mock import patch

from my_modules.Class_Mensagem_Log import id_msg, Class_Mensagem_Log
from my_modules.enum_timeframes import PERIOD_H1


@pytest.fixture(autouse=True)
def reset_class_dict():
    Class_Mensagem_Log.ultimo_envio_msg_exception_ids = {}
    yield
    Class_Mensagem_Log.ultimo_envio_msg_exception_ids = {}


def make_logger():
    return Class_Mensagem_Log(str(uuid.uuid4()))


# ── id_msg: ValueError e casos válidos ───────────────────────────────────────

class TestIdMsgValueErrors:

    def test_frequencia_seg_none(self):
        with pytest.raises(ValueError):
            id_msg(frequencia_seg=None, line=1, file="f.py")

    def test_frequencia_seg_not_int(self):
        with pytest.raises(ValueError):
            id_msg(frequencia_seg="300", line=1, file="f.py")

    def test_frequencia_seg_zero(self):
        obj = id_msg(frequencia_seg=0, line=1, file="f.py")
        assert obj.frequencia_seg == 0

    def test_frequencia_seg_negative(self):
        with pytest.raises(ValueError):
            id_msg(frequencia_seg=-1, line=1, file="f.py")

    def test_line_without_file(self):
        with pytest.raises(ValueError):
            id_msg(frequencia_seg=300, line=10)

    def test_file_without_line(self):
        with pytest.raises(ValueError):
            id_msg(frequencia_seg=300, file="f.py")

    def test_both_modes_given(self):
        with pytest.raises(ValueError):
            id_msg(frequencia_seg=300, line=1, file="f.py", function="fn")

    def test_valid_line_file(self):
        obj = id_msg(frequencia_seg=300, line=1, file="f.py")
        assert obj is not None

    def test_valid_function(self):
        obj = id_msg(frequencia_seg=300, function="fn")
        assert obj is not None

    def test_valid_auto_capture(self):
        obj = id_msg(frequencia_seg=300)
        assert obj is not None


# ── id_msg: auto-captura de linha e arquivo ──────────────────────────────────

class TestIdMsgAutoCapture:

    def test_auto_capture_line_and_file(self):
        expected_line = inspect.currentframe().f_lineno + 1
        obj = id_msg(frequencia_seg=300)
        expected_file = os.path.basename(__file__)
        assert obj.id() == f"|line|_{expected_line}_|file|_{expected_file}"

    def test_auto_capture_different_lines_produce_different_ids(self):
        obj_a = id_msg(frequencia_seg=300)
        obj_b = id_msg(frequencia_seg=300)
        assert obj_a.id() != obj_b.id()


# ── id_msg.id(): formato e tratamento de file ────────────────────────────────

class TestIdMsgIdMethod:

    def test_id_with_line_and_file(self):
        obj = id_msg(frequencia_seg=300, line=1234, file="Main.py")
        assert obj.id() == "|line|_1234_|file|_Main.py"

    def test_id_with_function(self):
        obj = id_msg(frequencia_seg=300, function="send_ping")
        assert obj.id() == "|func|_send_ping"

    def test_file_stored_as_basename_unix_path(self):
        obj = id_msg(frequencia_seg=300, line=5, file="/some/deep/path/Main.py")
        assert obj.id() == "|line|_5_|file|_Main.py"

    def test_file_stored_as_basename_windows_path(self):
        obj = id_msg(frequencia_seg=300, line=5, file=r"C:\Users\Luiz\project\Main.py")
        assert obj.id() == "|line|_5_|file|_Main.py"

    def test_file_stored_as_basename_full_path_no_extension(self):
        obj = id_msg(frequencia_seg=300, line=5, file="/some/path/script")
        assert obj.id() == "|line|_5_|file|_script"

    def test_file_stored_as_basename_name_only_no_extension(self):
        obj = id_msg(frequencia_seg=300, line=5, file="Main")
        assert obj.id() == "|line|_5_|file|_Main"


# ── id_msg: atributos privados inacessíveis ──────────────────────────────────

class TestIdMsgPrivateAttributes:

    def test_line_not_accessible(self):
        obj = id_msg(frequencia_seg=300, line=1, file="f.py")
        with pytest.raises(AttributeError):
            _ = obj.line

    def test_file_not_accessible(self):
        obj = id_msg(frequencia_seg=300, line=1, file="f.py")
        with pytest.raises(AttributeError):
            _ = obj.file

    def test_function_not_accessible(self):
        obj = id_msg(frequencia_seg=300, function="fn")
        with pytest.raises(AttributeError):
            _ = obj.function


# ── exception(): validação do parâmetro id ───────────────────────────────────

class TestExceptionIdValidation:

    def test_id_string_raises_type_error(self):
        logger = make_logger()
        with pytest.raises(TypeError):
            logger.exception("msg", id="not_an_id_msg")

    def test_id_none_auto_captura(self):
        logger = make_logger()
        # id=None deve capturar automaticamente o frame e usar frequencia=PERIOD_H1
        logger.exception("msg", id=None)


# ── exception(): EnviarServidorMsgs=False nunca chama servidor_msgs ─────────────

class TestExceptionNoServidorMsgsWhenDisabled:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_pushbullet_not_called_when_enviar_false(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=PERIOD_H1, line=1, file="f.py")
        logger.exception("test", id=msg_id, EnviarServidorMsgs=False)
        mock_send.assert_not_called()


# ── exception(): primeira chamada sempre envia ───────────────────────────────

class TestExceptionFirstCallSends:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_first_call_sends_pushbullet(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=PERIOD_H1, line=1, file="f.py")
        logger.exception("test", id=msg_id)
        mock_send.assert_called_once()


# ── exception(): segunda chamada dentro da janela é suprimida ────────────────

class TestExceptionWithinWindowSuppressed:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_second_call_within_window_suppressed(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=PERIOD_H1, line=1, file="f.py")

        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 10)  # 10 s < PERIOD_H1

        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t0
            logger.exception("test", id=msg_id)

        assert mock_send.call_count == 1

        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t1
            logger.exception("test", id=msg_id)

        assert mock_send.call_count == 1


# ── exception(): chamada após janela envia novamente ─────────────────────────

class TestExceptionAfterWindowSendsAgain:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_call_after_window_sends(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=PERIOD_H1, line=1, file="f.py")

        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t2 = datetime.datetime(2024, 1, 1, 13, 0, 1)  # 3601 s >= PERIOD_H1

        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t0
            logger.exception("test", id=msg_id)

        assert mock_send.call_count == 1

        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t2
            logger.exception("test", id=msg_id)

        assert mock_send.call_count == 2


# ── ultimo_envio_msg_exception_ids é atributo de classe (compartilhado) ──────

class TestClassLevelDict:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_dict_shared_between_instances(self, mock_is_set, mock_send):
        logger_a = make_logger()
        logger_b = make_logger()
        msg_id = id_msg(frequencia_seg=PERIOD_H1, line=1, file="f.py")

        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 10)  # dentro da janela

        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t0
            logger_a.exception("test", id=msg_id)

        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t1
            logger_b.exception("test", id=msg_id)

        assert mock_send.call_count == 1


# ── dict atualizado após envio ────────────────────────────────────────────────

class TestDictUpdatedAfterSend:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_dict_updated_after_send(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=PERIOD_H1, line=1, file="f.py")
        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)

        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t0
            logger.exception("test", id=msg_id)

        key = msg_id.id()
        assert key in Class_Mensagem_Log.ultimo_envio_msg_exception_ids
        assert Class_Mensagem_Log.ultimo_envio_msg_exception_ids[key] == t0


# ── id_msg: frequencia = 0 é válida ──────────────────────────────────────────

class TestIdMsgFrequenciaZero:

    def test_frequencia_zero_explicita(self):
        obj = id_msg(frequencia_seg=0, line=1, file="f.py")
        assert obj.frequencia_seg == 0

    def test_sem_args_frequencia_zero(self):
        obj = id_msg()
        assert obj.frequencia_seg == 0

    def test_frequencia_negativa_levanta_erro(self):
        with pytest.raises(ValueError):
            id_msg(frequencia_seg=-1, line=1, file="f.py")


# ── log.info / log.debug sem id ──────────────────────────────────────────────

class TestInfoDebugSemId:

    def test_info_sem_id_nao_levanta_erro(self):
        logger = make_logger()
        logger.info("msg sem id")

    def test_debug_sem_id_nao_levanta_erro(self):
        logger = make_logger()
        logger.debug("msg sem id")

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_info_sem_id_captura_frame_correto(self, mock_is_set, mock_send):
        logger = make_logger()
        expected_file = os.path.basename(__file__)
        with patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg") as mock_send2:
            with patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True):
                expected_line = inspect.currentframe().f_lineno + 1
                logger.info("msg", EnviarServidorMsgs=True)
        texto = mock_send2.call_args[0][0]
        assert f"|line|_{expected_line}_|file|_{expected_file}" in texto

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_debug_sem_id_captura_frame_correto(self, mock_is_set, mock_send):
        logger = make_logger()
        expected_file = os.path.basename(__file__)
        with patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg") as mock_send2:
            with patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True):
                expected_line = inspect.currentframe().f_lineno + 1
                logger.debug("msg", EnviarServidorMsgs=True)
        texto = mock_send2.call_args[0][0]
        assert f"|line|_{expected_line}_|file|_{expected_file}" in texto


# ── exception sem id ─────────────────────────────────────────────────────────

class TestExceptionSemId:

    def test_sem_id_nao_levanta_erro(self):
        logger = make_logger()
        logger.exception("msg sem id")

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_sem_id_envia_na_primeira_chamada(self, mock_is_set, mock_send):
        logger = make_logger()
        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = datetime.datetime(2024, 1, 1, 12, 0, 0)
            logger.exception("msg")
        mock_send.assert_called_once()


# ── exception(): frequência mínima de 1h ─────────────────────────────────────

class TestExceptionFrequenciaMinima:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_frequencia_menor_h1_emite_warning_no_log(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=60, line=1, file="f.py")
        with patch.object(logger.logger, "warning") as mock_warning:
            logger.exception("test", id=msg_id)
        mock_warning.assert_called_once()

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_frequencia_menor_h1_envia_warning_ao_servidor(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=60, line=1, file="f.py")
        logger.exception("test", id=msg_id)
        # primeira chamada = warning ao servidor + exception ao servidor = 2 envios
        assert mock_send.call_count == 2
        primeira_chamada = mock_send.call_args_list[0][0][0]
        assert "frequencia_seg=60s" in primeira_chamada

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_frequencia_igual_h1_sem_warning(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=PERIOD_H1, line=1, file="f.py")
        with patch.object(logger.logger, "warning") as mock_warning:
            logger.exception("test", id=msg_id)
        mock_warning.assert_not_called()
        mock_send.assert_called_once()

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_frequencia_menor_h1_throttle_usa_h1(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=60, line=1, file="f.py")

        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 5, 0)  # 5 min < PERIOD_H1

        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t0
            logger.exception("test", id=msg_id)

        call_count_after_first = mock_send.call_count  # 2: warning + exception

        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t1
            logger.exception("test", id=msg_id)

        # segunda chamada: warning reenviado, mas exception suprimida (5 min < PERIOD_H1)
        assert mock_send.call_count == call_count_after_first + 1
