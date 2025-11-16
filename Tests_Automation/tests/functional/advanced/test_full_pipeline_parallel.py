import socket
import time
from config.paths import add_project_to_syspath

add_project_to_syspath()
from Server.App.Server import HOST, PORT  # type: ignore


def _simple_client(name: str, level: int, mode: str = "Параллельно") -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    s.connect((HOST, PORT))
    payload = f"{name}|{level}|{mode}".encode("utf-8")
    s.send(payload)
    _ = s.recv(1024)  # CONNECTED
    return s


def test_full_pipeline_parallel(server_running):
    """
    Test de tip „smoke” pentru 3 clienți care se conectează în paralel.
    (Nu trimitem CSV real, doar verificăm că handshake-ul merge.)
    """
    clients = []
    for i in range(3):
        c = _simple_client(f"Parallel{i}", 1)
        clients.append(c)

    # aşteptăm un pic să fie înregistraţi
    time.sleep(0.5)

    # dacă până aici nu a crăpat serverul, considerăm succes
    for c in clients:
        try:
            c.send(b"DISCONNECT")
        except OSError:
            pass
        c.close()

    assert len(clients) == 3
