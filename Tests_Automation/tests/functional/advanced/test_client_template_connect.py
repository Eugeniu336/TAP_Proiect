import socket
from config.paths import add_project_to_syspath

add_project_to_syspath()
from Client.Client_Template import Client_Template as ct  # type: ignore
from Server.App.Server import HOST, PORT  # type: ignore


def test_client_template_can_connect(server_running):
    """
    Verifică faptul că un socket simplu se poate conecta la server și poate trimite
    un mesaj de handshake compatibil cu protocolul.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    s.connect((HOST, PORT))

    # trimitem mesaj de înregistrare asemănător cu clientul real
    name = "TestClient"
    level = "1"
    mode = "Параллельно"
    handshake = f"{name}|{level}|{mode}".encode("utf-8")
    s.send(handshake)

    # serverul ar trebui să răspundă cu "CONNECTED" sau "ERROR:..."
    resp = s.recv(1024).decode("utf-8")
    assert "ERROR" not in resp
    assert "CONNECTED" in resp

    s.close()
