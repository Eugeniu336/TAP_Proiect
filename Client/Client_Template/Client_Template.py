import socket
import threading
import tkinter as tk
from tkinter import messagebox
import struct
import json
from pathlib import Path
import time

SERVER_IP = "127.0.0.1"
PORT = 9090

CLIENT_NAME = "Name"
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
    """
    Заглушка для реальной задачи.
    (づ｡◕‿‿◕｡)づ 
    """
    work = "Результат работы клиента"
    return work, None  # Возвращаем кортеж (результат, новый_csv)

# ======================= Слушатель сервера =======================
def listen_server():
    global connected, csv_data, csv_file_path, processed_count
    
    while connected:
        try:
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
            
            # Если не файл, читаем как команду
            client_socket.settimeout(None)
            msg = client_socket.recv(1024).decode('utf-8')
            
            if not msg:
                break
                
            if msg == "DISCONNECT":
                messagebox.showinfo("Сервер", "Вы были отключены сервером.")
                disconnect()
                break
                
            elif msg.startswith("ERROR:"):
                messagebox.showerror("Ошибка", msg.replace("ERROR:", "").strip())
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
                messagebox.showerror("Ошибка", msg.replace("ERROR:", "").strip())
                client_socket.close()
                return
        except socket.timeout:
            pass
        client_socket.settimeout(None)

        connected = True
        threading.Thread(target=listen_server, daemon=True).start()
        status_label.config(text=f"Подключен к {SERVER_IP}:{PORT}", fg="green")
        messagebox.showinfo("Успех", f"Подключено к серверу {SERVER_IP}:{PORT}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось подключиться к серверу {SERVER_IP}:{PORT}.\n{e}")

def disconnect():
    global connected
    if not connected:
        return
    try:
        client_socket.close()
    except:
        pass
    connected = False
    status_label.config(text="Отключен", fg="red")

def open_settings():
    """Окно настроек для изменения IP и порта."""
    settings = tk.Toplevel()
    settings.title("Настройки сервера")
    settings.geometry("300x160")
    settings.resizable(False, False)

    tk.Label(settings, text="IP сервера:").pack(pady=5)
    ip_entry = tk.Entry(settings)
    ip_entry.insert(0, SERVER_IP)
    ip_entry.pack(pady=5)

    tk.Label(settings, text="Порт:").pack(pady=5)
    port_entry = tk.Entry(settings)
    port_entry.insert(0, str(PORT))
    port_entry.pack(pady=5)

    def save_settings():
        global SERVER_IP, PORT
        try:
            new_ip = ip_entry.get().strip()
            new_port = int(port_entry.get().strip())
            if not new_ip:
                raise ValueError
            SERVER_IP = new_ip
            PORT = new_port
            messagebox.showinfo("Сохранено", f"Новый сервер: {SERVER_IP}:{PORT}")
            settings.destroy()
        except:
            messagebox.showerror("Ошибка", "Некорректный IP или порт.")

    tk.Button(settings, text="Сохранить", command=save_settings).pack(pady=10)

# ============================================= GUI =============================================
def create_gui():
    global status_label
    root = tk.Tk()
    root.title(f"Клиент — {CLIENT_NAME}")
    root.geometry("300x250")
    root.resizable(False, False)

    tk.Label(root, text=f"Имя: {CLIENT_NAME}", font=("Arial", 12)).pack(pady=5)
    tk.Label(root, text=f"Уровень: {CLIENT_LEVEL}, Режим: {CLIENT_MODE}", font=("Arial", 10)).pack(pady=2)

    status_label = tk.Label(root, text="Отключен", fg="red", font=("Arial", 12))
    status_label.pack(pady=10)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Подключиться", command=connect, width=12).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Отключиться", command=disconnect, width=12).pack(side=tk.LEFT, padx=5)

    tk.Button(root, text="⚙ Настройки сервера", command=open_settings, width=25).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()