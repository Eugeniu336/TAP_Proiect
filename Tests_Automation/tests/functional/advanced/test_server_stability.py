import socket
import time
from config.paths import add_project_to_syspath

add_project_to_syspath()
from Server.App.Server import HOST, PORT  # type: ignore


def test_server_stability_short_ping(server_running):
    """
    Trimite câteva „ping-uri” scurte la server pentru a vedea
    că nu se prăbuşeşte sub load mic.
    """
    for i in range(3):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((HOST, PORT))
        s.send(f"PingClient{i}|1|Параллельно".encode("utf-8"))
        _ = s.recv(1024)  # CONNECTED / ERROR
        s.send(b"DISCONNECT")
        s.close()
        time.sleep(0.1)

    assert True
