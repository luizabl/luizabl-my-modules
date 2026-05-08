import os
import pytest

from my_modules.Pushbullet_Class import Pushbullet_Class


pytestmark = pytest.mark.skipif(
    not os.environ.get("PushBullet_APIKEY"),
    reason="PushBullet_APIKEY não definida no .env — skip integração",
)


class TestPushbulletIntegracao:

    def test_is_set_com_env_vars(self):
        pb = Pushbullet_Class()
        assert pb.PushbulletIsSet() is True

    def test_envio_mensagem_real(self):
        pb = Pushbullet_Class()
        pb.PushbulletSet(os.environ["PushBullet_APIKEY"], IntervaloMinimo_seg=1)
        pb.PushbulletSendMsg("[TESTE DE INTEGRAÇÃO] Pushbullet_Class.PushbulletSendMsg", ForcarEnvio=True)
