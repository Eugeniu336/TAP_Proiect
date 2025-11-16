import socket
import time
from threading import Thread

from config.paths import add_project_to_syspath

add_project_to_syspath()
from Server.App.Server import HOST, PORT  # type: ignore


def _client_job(idx: int, results: list[str]):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3.0)
        s.connect((HOST, PORT))
        s.send(f"LoadClient{idx}|1|Параллельно".encode("utf-8"))
        resp = s.recv(1024).decode("utf-8")
        results.append(resp)
        s.send(b"DISCONNECT")
        s.close()
    except Exception as e:
        results.append(f"ERR:{e}")


def test_parallel_clients(server_running):
    """
    Porneşte 5 clienţi în paralel care se conectează la server.
    Verificăm că majoritatea conexiunilor primesc un răspuns valid.
    """
    threads = []
    results: list[str] = []

    for i in range(5):
        t = Thread(target=_client_job, args=(i, results))
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=5.0)

    # cel puţin 3 din 5 trebuie să aibă CONNECTED
    ok = sum("CONNECTED" in r for r in results)
    assert ok >= 3
