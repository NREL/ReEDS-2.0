import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).absolute().parents[1]))
from server import REEDS


@pytest.fixture()
def cli(loop, aiohttp_client):
    server_ = REEDS()
    yield loop.run_until_complete(aiohttp_client(server_.app))
    loop.run_until_complete(server_.cleanup_background_tasks())