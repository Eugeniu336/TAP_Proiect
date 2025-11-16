import socket
import threading
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QListWidget, QVBoxLayout, QHBoxLayout, \
    QMessageBox
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QObject
import pandas as pd
import time
import os
import struct
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from App_Functions.CSV_Manager import load_initial_csv
from App_Functions.Results_Window import show_results_window
from App_Functions.Workflow_Manager import WorkflowManager, set_csv_data


# ===================================== Настройки сервера =====================================
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


HOST = get_local_ip()
PORT = 9090

clients = {}
names = set()
server_running = True

# Папки для файлов
RECEIVED_DIR = Path("received_from_clients")
RECEIVED_DIR.mkdir(exist_ok=True)


# ===================================== Передача файлов =====================================
def recv_exact(conn: socket.socket, n: int) -> bytes:
    """Получение точного количества байт"""
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed by client")
        buf.extend(chunk)
    return bytes(buf)


def send_message(conn: socket.socket, header: dict, data: bytes):
    """Отправка структурированного сообщения"""
    header_bytes = json.dumps(header).encode('utf-8')
    conn.sendall(struct.pack(">I", len(header_bytes)))
    conn.sendall(header_bytes)
    if data:
        conn.sendall(data)


def recv_message(conn: socket.socket):
    """Получение структурированного сообщения"""
    raw = conn.recv(4)
    if not raw:
        return None, None
    header_len = struct.unpack(">I", raw)[0]
    header_bytes = recv_exact(conn, header_len)
    header = json.loads(header_bytes.decode('utf-8'))
    size = header.get("size", 0)
    data = recv_exact(conn, size) if size > 0 else b""
    return header, data


def send_file_to_client(conn, filepath):
    """Отправка файла клиенту"""
    if not os.path.exists(filepath):
        print(f"[!] File not found: {filepath}")
        return False

    with open(filepath, 'rb') as f:
        data = f.read()

    filename = os.path.basename(filepath)
    header = {
        "action": "send_file",
        "filename": filename,
        "size": len(data)
    }

    send_message(conn, header, data)
    print(f"[-->] Sent file {filename} ({len(data)} bytes)")
    return True


def receive_file_from_client(conn):
    """Получение файла от клиента"""
    header, data = recv_message(conn)
    return header, data


# ===================================== Работа с клиентами =====================================
def handle_client(conn, addr):
    try:
        conn.settimeout(5)
        data = conn.recv(1024).decode('utf-8')
        name, level, mode = data.split('|')

        if name in names:
            conn.send("ERROR: Name already in use".encode('utf-8'))
            conn.close()
            return

        clients[addr] = (conn, name, int(level), mode)
        names.add(name)
        conn.send("CONNECTED".encode('utf-8'))

        conn.settimeout(None)

        # Сигнал для обновления GUI
        gui_signals.update_list.emit()
        print(f"[+] Client connected: {name} (Lvl {level}, {mode}) — {addr}")

        # Держим соединение открытым
        while True:
            time.sleep(1)

    except socket.timeout:
        print(f"[!] Connection timeout {addr}")
    except Exception as e:
        print(f"[!] Client error {addr}: {e}")
    finally:
        if addr in clients:
            disconnect_client(addr, silent=True)


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER STARTED] {HOST}:{PORT}")
    threading.Thread(target=accept_clients, args=(server,), daemon=True).start()


def accept_clients(server):
    while server_running:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except:
            break


def disconnect_client(addr, silent=False):
    if addr not in clients:
        return
    conn, name, _, _ = clients[addr]
    try:
        conn.send("DISCONNECT".encode('utf-8'))
        conn.close()
    except:
        pass
    del clients[addr]
    if name in names:
        names.remove(name)
    if not silent:
        print(f"[-] Client disconnected: {name}")
    gui_signals.update_list.emit()


def disconnect_all():
    for addr in list(clients.keys()):
        disconnect_client(addr, silent=True)
    gui_signals.update_list.emit()


# ===================================== Запуск работы клиентов =====================================
def request_work_from_clients():
    """Запуск рабочего процесса через WorkflowManager"""
    if not clients:
        QMessageBox.information(None, "Info", "No connected clients.")
        return

    # Создаём WorkflowManager с callback'ами
    workflow = WorkflowManager(
        clients_dict=clients,
        send_file_func=send_file_to_client,
        receive_file_func=receive_file_from_client,
        send_message_func=send_message,
        update_callback=lambda delay, func: QApplication.instance().processEvents() or func(),
        results_callback=show_results_window
    )

    # Запускаем workflow
    workflow.start_workflow()


# ===================================== GUI Signals =====================================
class GUISignals(QObject):
    update_list = pyqtSignal()


gui_signals = GUISignals()


# ===================================== GUI =====================================
class ServerWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Без рамки
        self.setWindowFlags(Qt.FramelessWindowHint)
        # Прозрачность окна
        self.setAttribute(Qt.WA_TranslucentBackground)

        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        UI_DIR = os.path.join(ROOT_DIR, "App_UI")

        # Путь к единственной текстуре
        texture_file = os.path.join(UI_DIR, "app_ui.png")

        # Проверяем наличие файла и грузим фон
        if os.path.exists(texture_file):
            self.background = QPixmap(texture_file)
            self.resize(self.background.width(), self.background.height())
        else:
            # Если нет текстуры — обычное окно
            self.setWindowFlags(Qt.Window)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            self.resize(800, 600)
            self.background = None

        self.drag_pos = QPoint()

        # Заголовок
        self.title_label = QLabel(f"Server: {HOST}:{PORT}", self)
        self.title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.move(175, 675)
        self.title_label.setFixedSize(450, 50)

        # Список клиентов
        self.client_list = QListWidget(self)
        self.client_list.move(84, 270)
        self.client_list.setFixedSize(640, 200)
        self.client_list.setStyleSheet("""
            color: white;
            font-size: 14px;
            background-color: transparent;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            border-bottom-left-radius: 15px;
            border-bottom-right-radius: 15px;
        """)

        # Кнопки
        btn_style = """
            background-color: #4CAF50;
            color: white;
            font-size: 12px;
            border-radius: 10px;
        """

        # Кнопка "Отключить выбранного"
        self.btn_disconnect_one = QPushButton("Disconnect\nSelected", self)
        self.btn_disconnect_one.move(75, 525)
        self.btn_disconnect_one.setFixedSize(175, 75)
        self.btn_disconnect_one.setStyleSheet(btn_style + """
            background-color: #9BB4C0;
            color: black;
            font-size: 20px;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            border-bottom-left-radius: 60px;
            border-bottom-right-radius: 15px;
        """)
        self.btn_disconnect_one.clicked.connect(self.on_disconnect_one)

        # Кнопка "Отключить всех"
        self.btn_disconnect_all = QPushButton("Disconnect\nAll", self)
        self.btn_disconnect_all.move(275, 525)
        self.btn_disconnect_all.setFixedSize(120, 75)
        self.btn_disconnect_all.setStyleSheet(btn_style + """
            background-color: #9BB4C0;
            color: black;
            font-size: 20px;
            border-top-left-radius: 15px;
            border-top-right-radius: 5px;
            border-bottom-left-radius: 15px;
            border-bottom-right-radius: 5px;
        """)
        self.btn_disconnect_all.clicked.connect(disconnect_all)

        # Кнопка "Запросить do_work()"
        self.btn_request_work = QPushButton("Start\nWork", self)
        self.btn_request_work.move(405, 525)
        self.btn_request_work.setFixedSize(120, 75)
        self.btn_request_work.setStyleSheet("""
            background-color: #9BB4C0;
            color: black;
            font-size: 20px;
            border-top-left-radius: 5px;
            border-top-right-radius: 15px;
            border-bottom-left-radius: 5px;
            border-bottom-right-radius: 15px;
        """)
        self.btn_request_work.clicked.connect(request_work_from_clients)

        # Кнопка "Показать результаты"
        self.btn_show_results = QPushButton("Show\nResults", self)
        self.btn_show_results.move(550, 525)
        self.btn_show_results.setFixedSize(175, 75)
        self.btn_show_results.setStyleSheet("""
            background-color: #9BB4C0;
            color: black;
            font-size: 20px;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            border-bottom-left-radius: 15px;
            border-bottom-right-radius: 60px;
        """)
        self.btn_show_results.clicked.connect(show_results_window)

        # Кнопка минимизации
        self.btn_minimize = QPushButton("−", self)
        self.btn_minimize.move(100, 675)
        self.btn_minimize.setFixedSize(50, 50)
        self.btn_minimize.setStyleSheet(btn_style)
        self.btn_minimize.clicked.connect(self.showMinimized)

        # Кнопка закрытия
        self.btn_close = QPushButton("×", self)
        self.btn_close.move(650, 675)
        self.btn_close.setFixedSize(50, 50)
        self.btn_close.setStyleSheet(btn_style)
        self.btn_close.clicked.connect(self.close)

        # Подключение сигнала обновления списка
        gui_signals.update_list.connect(self.update_client_list)

        # Загрузка начальных CSV данных
        csv_data, csv_file = load_initial_csv()
        if csv_data and csv_file:
            set_csv_data(csv_data, csv_file)

        # Запуск сервера
        start_server()

    def paintEvent(self, event):
        """Рисуем фон"""
        if self.background:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.background)

    def mousePressEvent(self, event):
        """Перемещение окна"""
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)

    def update_client_list(self):
        """Обновление списка клиентов"""
        self.client_list.clear()
        for addr, (_, name, level, mode) in clients.items():
            self.client_list.addItem(f"{name} (Lvl {level}, {mode}) — {addr[0]}")

    def on_disconnect_one(self):
        """Отключение выбранного клиента"""
        current_row = self.client_list.currentRow()
        if current_row == -1:
            QMessageBox.information(self, "Info", "Select a client to disconnect.")
            return
        addr = list(clients.keys())[current_row]
        disconnect_client(addr)


# ===================================== Main =====================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ServerWindow()
    window.show()
    sys.exit(app.exec_())