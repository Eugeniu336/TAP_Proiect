import sys
import socket
import threading
import struct
import json
from pathlib import Path
import time

from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QMessageBox,
                             QDialog, QVBoxLayout, QLineEdit, QTextEdit)
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QObject

SERVER_IP = "127.0.0.1"  # placeholder
PORT = 9090

CLIENT_NAME = "NameNameName"
CLIENT_LEVEL = "1"
CLIENT_MODE = "Параллельно"

client_socket = None
connected = False

csv_file_path = None
csv_data = None
processed_count = 0

# Папки для файлов
RECV_DIR = Path("received_files")
PROCESSED_DIR = Path("processed_files")
RECV_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)


# ======================= Сигналы для обновления GUI =======================
class Signals(QObject):
    status_changed = pyqtSignal(str, str)  # text, color
    show_info = pyqtSignal(str, str)  # title, message
    show_error = pyqtSignal(str, str)  # title, message

signals = Signals()


# ======================= Функции передачи данных =======================
def recv_exact(sock, n):
    """Получение точного количества байт"""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Соединение прервано")
        buf.extend(chunk)
    return bytes(buf)


def recv_message(sock):
    """Получение структурированного сообщения"""
    raw = sock.recv(4)
    if not raw:
        return None, None

    header_len = struct.unpack(">I", raw)[0]
    header_bytes = recv_exact(sock, header_len)
    header = json.loads(header_bytes.decode('utf-8'))

    size = header.get("size", 0)
    data = recv_exact(sock, size) if size > 0 else b""
    return header, data


def send_message(sock, header, data):
    """Отправка структурированного сообщения"""
    header_bytes = json.dumps(header).encode('utf-8')
    sock.sendall(struct.pack(">I", len(header_bytes)))
    sock.sendall(header_bytes)
    if data:
        sock.sendall(data)


# ======================= Основная функция работы =======================
def do_work():
    work = "Результат работы клиента"

    """
    Заглушка для реальной задачи.
    (づ｡◕‿‿◕｡)づ 
    """
    return work, None  # Возвращаем кортеж (результат, новый_csv)


# ======================= Слушатель сервера =======================
def listen_server():
    global connected, csv_data, csv_file_path, processed_count

    while connected:
        try:
            if not connected or client_socket is None:
                break

            client_socket.settimeout(1.0)

            try:
                peek = client_socket.recv(4, socket.MSG_PEEK)
                if not peek:
                    continue

                # Проверяем, это файл или команда
                try:
                    header_len = struct.unpack(">I", peek)[0]
                    if 0 < header_len < 10000:
                        # Это структурированное сообщение (файл)
                        client_socket.settimeout(None)
                        header, data = recv_message(client_socket)

                        if header and header.get("action") == "send_file":
                            filename = header.get("filename", "received.csv")

                            # Сохраняем файл
                            save_path = RECV_DIR / filename
                            i = 1
                            base, suff = save_path.stem, save_path.suffix
                            while save_path.exists():
                                save_path = RECV_DIR / f"{base}_{i}{suff}"
                                i += 1

                            with open(save_path, 'wb') as f:
                                f.write(data)

                            # Загружаем CSV в память
                            csv_data = data.decode('utf-8')
                            csv_file_path = save_path
                            print(f"[CSV] Получен файл {filename} ({len(data)} байт) -> {save_path}")
                        continue
                except (struct.error, UnicodeDecodeError):
                    pass

            except socket.timeout:
                continue
            except (OSError, ConnectionError):
                # Сокет закрыт или соединение потеряно
                break

            # Если не файл, читаем как команду
            if not connected or client_socket is None:
                break

            client_socket.settimeout(None)
            msg = client_socket.recv(1024).decode('utf-8')

            if not msg:
                break

            if msg == "DISCONNECT":
                signals.show_info.emit("Сервер", "Вы были отключены сервером.")
                disconnect()
                break

            elif msg.startswith("ERROR:"):
                signals.show_error.emit("Ошибка", msg.replace("ERROR:", "").strip())
                disconnect()
                break

            elif msg == "WORK":
                print("[WORK] Запрос на выполнение работы")
                result, new_csv = do_work()

                if processed_count == 0:
                    print(result)
                    processed_count += 1

                # Отправляем текстовый результат
                client_socket.send(result.encode('utf-8'))
                time.sleep(0.3)

                # Отправляем обработанный файл обратно
                if new_csv:
                    processed_data = new_csv.encode('utf-8')

                    # Сохраняем локально
                    processed_path = PROCESSED_DIR / f"processed_{CLIENT_NAME}.csv"
                    with open(processed_path, 'wb') as f:
                        f.write(processed_data)

                    # Отправляем серверу
                    header = {
                        "action": "return_file",
                        "filename": f"processed_{CLIENT_NAME}.csv",
                        "size": len(processed_data)
                    }
                    send_message(client_socket, header, processed_data)
                    print(f"[CSV] Отправлен обработанный файл ({len(processed_data)} байт)")
                else:
                    print("[!] Нет обновлений для отправки")
                    no_update_data = b"NO_UPDATE"
                    header = {
                        "action": "return_file",
                        "filename": "no_update.txt",
                        "size": len(no_update_data)
                    }
                    send_message(client_socket, header, no_update_data)

        except socket.timeout:
            continue
        except (OSError, ConnectionError) as e:
            # Сокет закрыт или ошибка соединения
            print(f"[!] Соединение прервано: {e}")
            break
        except Exception as e:
            print(f"[!] Ошибка при получении данных: {e}")
            import traceback
            traceback.print_exc()
            break

    if connected:
        disconnect()


def connect():
    global client_socket, connected, SERVER_IP, PORT
    if connected:
        return
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, PORT))
        data = f"{CLIENT_NAME}|{CLIENT_LEVEL}|{CLIENT_MODE}"
        client_socket.send(data.encode('utf-8'))

        client_socket.settimeout(2)
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if msg.startswith("ERROR:"):
                signals.show_error.emit("Ошибка", msg.replace("ERROR:", "").strip())
                client_socket.close()
                return
        except socket.timeout:
            pass
        client_socket.settimeout(None)

        connected = True
        threading.Thread(target=listen_server, daemon=True).start()
        signals.status_changed.emit(f"Подключен к {SERVER_IP}:{PORT}", "green")
        signals.show_info.emit("Успех", f"Подключено к серверу {SERVER_IP}:{PORT}")
    except Exception as e:
        signals.show_error.emit("Ошибка", f"Не удалось подключиться к серверу {SERVER_IP}:{PORT}.\n{e}")


def disconnect():
    global connected, client_socket
    if not connected:
        return

    # Уведомляем сервер об отключении
    try:
        if client_socket:
            client_socket.send(b"DISCONNECT")
            time.sleep(0.1)  # Даём время на отправку
    except:
        pass

    connected = False  # Останавливаем поток

    try:
        if client_socket:
            client_socket.close()
            client_socket = None
    except:
        pass

    signals.status_changed.emit("Отключен", "red")


# ======================= Диалог настроек =======================
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки сервера")
        self.setFixedSize(300, 160)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("IP сервера:"))
        self.ip_entry = QLineEdit(SERVER_IP)
        layout.addWidget(self.ip_entry)

        layout.addWidget(QLabel("Порт:"))
        self.port_entry = QLineEdit(str(PORT))
        layout.addWidget(self.port_entry)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_settings(self):
        global SERVER_IP, PORT
        try:
            new_ip = self.ip_entry.text().strip()
            new_port = int(self.port_entry.text().strip())
            if not new_ip:
                raise ValueError
            SERVER_IP = new_ip
            PORT = new_port
            QMessageBox.information(self, "Сохранено", f"Новый сервер: {SERVER_IP}:{PORT}")
            self.accept()
        except:
            QMessageBox.critical(self, "Ошибка", "Некорректный IP или порт.")


# ======================= Главное окно =======================
class CustomWindow(QWidget):
    def __init__(self, level):
        super().__init__()

        # Без рамки
        self.setWindowFlags(Qt.FramelessWindowHint)
        # Прозрачность окна
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Текстуры по уровню
        import os
        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        UI_DIR = os.path.join(ROOT_DIR, "Client_UI")

        # Словарь текстур
        textures = {
            1: os.path.join(UI_DIR, "green_cartridge.png"),
            2: os.path.join(UI_DIR, "blue_cartridge.png"),
            3: os.path.join(UI_DIR, "yellow_cartridge.png"),
            4: os.path.join(UI_DIR, "red_cartridge.png"),
            5: os.path.join(UI_DIR, "red_cartridge.png"),
            6: os.path.join(UI_DIR, "violet_cartridge.png"),
            7: os.path.join(UI_DIR, "violet_cartridge.png")
        }

        level = int(CLIENT_LEVEL)
        texture_file = textures.get(level, textures[1])
        self.background = QPixmap(texture_file)
        self.resize(self.background.width(), self.background.height())

        self.drag_pos = QPoint()

        # ----------- 2 текстовые надписи -----------
        self.text1 = QLabel(CLIENT_NAME, self)
        self.text1.setFixedSize(200, 40)
        self.text1.move(70, 55)
        self.text1.setStyleSheet("color: white; font-size: 18px;")

        self.text2 = QTextEdit("Отключен", self)
        self.text2.setFixedSize(170, 80)
        self.text2.move(65, 110)
        self.text2.setReadOnly(True)
        self.text2.setStyleSheet("color: red; font-size: 18px;")

        # ----------- 3 кнопки -----------
        button_colors = {
            1: "background-color: #5C6F2E; color: black; border-radius: 8px;",
            2: "background-color: #284F5E; color: white; border-radius: 8px;",
            3: "background-color: #E9B63B; color: black; border-radius: 8px;",
            4: "background-color: #BA4125; color: black; border-radius: 8px;",
            5: "background-color: #BA4125; color: black; border-radius: 8px;",
            6: "background-color: #BB5C9C; color: black; border-radius: 8px;",
            7: "background-color: #BB5C9C; color: black; border-radius: 8px;",
        }
        btn_style = button_colors.get(level, "background-color: gray; color: black; border-radius: 8px;")

        self.btn1 = QPushButton("START", self)
        self.btn1.move(60, 210)
        self.btn1.setFixedSize(60, 30)
        self.btn1.setStyleSheet(btn_style)
        self.btn1.clicked.connect(connect)

        self.btn2 = QPushButton("STOP", self)
        self.btn2.move(180, 210)
        self.btn2.setFixedSize(60, 30)
        self.btn2.setStyleSheet(btn_style)
        self.btn2.clicked.connect(disconnect)

        self.btn3 = QPushButton("⚙", self)
        self.btn3.move(135, 210)
        self.btn3.setFixedSize(30, 30)
        self.btn3.setStyleSheet(btn_style)
        self.btn3.clicked.connect(self.open_settings)

        # Подключаем сигналы
        signals.status_changed.connect(self.update_status)
        signals.show_info.connect(self.show_info_message)
        signals.show_error.connect(self.show_error_message)

    # Рисуем фон
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.background)

    # Перемещение окна
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)

    def update_status(self, text, color):
        self.text2.setText(text)
        self.text2.setStyleSheet(f"color: {color}; font-size: 18px;")

    def show_info_message(self, title, message):
        QMessageBox.information(self, title, message)

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()


# ======================= Запуск =======================
def create_gui():
    """Функция для запуска GUI (для совместимости с плагинами)"""
    LEVEL = int(CLIENT_LEVEL)

    app = QApplication(sys.argv)
    window = CustomWindow(LEVEL)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    create_gui()