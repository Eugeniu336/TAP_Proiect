import socket
import pytest

from config.paths import add_project_to_syspath

add_project_to_syspath()
from Server.App.Server import HOST as SERVER_HOST, PORT as SERVER_PORT  # type: ignore


def _can_connect() -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect((SERVER_HOST, SERVER_PORT))
        return True
    except OSError:
        return False
    finally:
        s.close()


@pytest.fixture(scope="session")
def server_running():
    """
    Fixture care verifică dacă serverul e deja pornit.
    Dacă NU e pornit, testele care au nevoie îl vor marca ca 'skipped'.
    """
    if not _can_connect():
        pytest.skip(f"Serverul nu este pornit pe {SERVER_HOST}:{SERVER_PORT}")
    return True
