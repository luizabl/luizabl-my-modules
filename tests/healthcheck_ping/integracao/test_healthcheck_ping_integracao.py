import os

import pytest

from my_modules.healthcheck_ping import Healthcheck_ping


pytestmark = pytest.mark.skipif(
    not (os.environ.get("HEALTHCHECK_URL") and os.environ.get("HEALTHCHECK_TOKEN")),
    reason="HEALTHCHECK_URL e HEALTHCHECK_TOKEN nao definidos no .env",
)


def test_ping_real_no_servico_teste():
    assert Healthcheck_ping("SERVICO_TESTE") == "OK"
