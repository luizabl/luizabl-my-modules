import uuid
import inspect
import os
import datetime
import pytest
from unittest.mock import patch

from my_modules.Class_Mensagem_Log import id_msg, Class_Mensagem_Log


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
        with pytest.raises(ValueError):
            id_msg(frequencia_seg=0, line=1, file="f.py")

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

    def test_id_none_raises_type_error(self):
        logger = make_logger()
        with pytest.raises(TypeError):
            logger.exception("msg", id=None)


# ── exception(): EnviarServidorMsgs=False nunca chama servidor_msgs ─────────────

class TestExceptionNoServidorMsgsWhenDisabled:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_pushbullet_not_called_when_enviar_false(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=300, line=1, file="f.py")
        logger.exception("test", id=msg_id, EnviarServidorMsgs=False)
        mock_send.assert_not_called()


# ── exception(): primeira chamada sempre envia ───────────────────────────────

class TestExceptionFirstCallSends:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_first_call_sends_pushbullet(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=300, line=1, file="f.py")
        logger.exception("test", id=msg_id)
        mock_send.assert_called_once()


# ── exception(): segunda chamada dentro da janela é suprimida ────────────────

class TestExceptionWithinWindowSuppressed:

    @patch.object(Class_Mensagem_Log, "servidor_msgs_SendMsg")
    @patch.object(Class_Mensagem_Log, "servidor_msgs_IsSet", return_value=True)
    def test_second_call_within_window_suppressed(self, mock_is_set, mock_send):
        logger = make_logger()
        msg_id = id_msg(frequencia_seg=300, line=1, file="f.py")

        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t1 = datetime.datetime(2024, 1, 1, 12, 0, 10)  # 10 s < 300 s

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
        msg_id = id_msg(frequencia_seg=300, line=1, file="f.py")

        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)
        t2 = datetime.datetime(2024, 1, 1, 12, 5, 1)  # 301 s >= 300 s

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
        msg_id = id_msg(frequencia_seg=300, line=1, file="f.py")

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
        msg_id = id_msg(frequencia_seg=300, line=1, file="f.py")
        t0 = datetime.datetime(2024, 1, 1, 12, 0, 0)

        with patch("my_modules.Class_Mensagem_Log.dt") as mock_dt:
            mock_dt.datetime.now.return_value = t0
            logger.exception("test", id=msg_id)

        key = msg_id.id()
        assert key in Class_Mensagem_Log.ultimo_envio_msg_exception_ids
        assert Class_Mensagem_Log.ultimo_envio_msg_exception_ids[key] == t0
