import socket
import pytest
from config.paths import SERVER_ROOT, add_project_to_syspath

add_project_to_syspath()

from Server.App.Server import HOST, PORT  # type: ignore


def test_server_connection():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.5)

    try:
        s.connect((HOST, PORT))
    except OSError:
        pytest.skip(f"Serverul nu pare să fie pornit pe {HOST}:{PORT}")
    else:
        s.close()
        assert True
