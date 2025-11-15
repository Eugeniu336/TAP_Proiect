import socket
import threading
import tkinter as tk
from tkinter import messagebox

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

def do_work():
    work = "Результат работы клиента"
    """
    Заглушка для реальной задачи.
    (づ｡◕‿‿◕｡)づ 
    """
    return work, None  # Возвращаем кортеж (результат, новый_csv)


def listen_server():
    global connected, csv_data, processed_count
    while connected:
        try:
            # ВАЖНО: НЕ блокируем если нет данных
            client_socket.settimeout(1.0)  # 1 секунда таймаут для проверки
            
            try:
                first_bytes = client_socket.recv(10, socket.MSG_PEEK).decode('utf-8', errors='ignore')
            except socket.timeout:
                continue  # Просто продолжаем ждать
            
            client_socket.settimeout(None)  # Убираем таймаут
            
            if first_bytes.startswith("SIZE:"):
                full_data = receive_large_data(client_socket)
                if full_data.startswith("CSV_DATA:"):
                    csv_data = full_data.replace("CSV_DATA:", "").strip()
                    print(f"[CSV] Получены данные ({len(csv_data)} символов)")
                continue
                
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
                print("[Сервер] -> Запрос на выполнение работы")
                result, new_csv_data = do_work()
                
                if processed_count == 0:
                    print(result)
                    processed_count += 1
                
                client_socket.send(result.encode('utf-8'))
                import time
                time.sleep(0.3)
                
                if new_csv_data:
                    send_large_data(client_socket, f"CSV_UPDATED:{new_csv_data}")
                    print(f"[CSV] Отправлены обновлённые данные ({len(new_csv_data)} байт)")
                else:
                    send_large_data(client_socket, "NO_UPDATE")
                    
        except socket.timeout:
            continue  # Нормально, просто продолжаем
        except Exception as e:
            print(f"[!] Ошибка при получении данных: {e}")
            import traceback
            traceback.print_exc()
            break  # Выходим только при критической ошибке
    
    # Если вышли из цикла - отключаемся
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

        # Проверим подтверждение подключения
        client_socket.settimeout(2)
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if msg.startswith("ERROR:"):
                messagebox.showerror("Ошибка", msg.replace("ERROR:", "").strip())
                client_socket.close()
                return
            # Просто подтверждаем подключение, CSV получим позже
        except socket.timeout:
            pass
        client_socket.settimeout(None)

        connected = True
        threading.Thread(target=listen_server, daemon=True).start()
        status_label.config(text=f"Подключен к {SERVER_IP}:{PORT}", fg="green")
        messagebox.showinfo("Успех", f"Подключено к серверу {SERVER_IP}:{PORT}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось подключиться к серверу {SERVER_IP}:{PORT}.\n{e}")

def receive_large_data(sock, timeout=180):  # Увеличен таймаут
    sock.settimeout(timeout)
    size_header = b""
    while b"\n" not in size_header:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("Соединение прервано")
        size_header += chunk

    size_str = size_header.decode('utf-8').strip()
    if not size_str.startswith("SIZE:"):
        raise ValueError("Неверный формат заголовка")
    total_size = int(size_str.replace("SIZE:", ""))
    print(f"[RECV] Ожидается {total_size} байт")

    received_data = b""
    while len(received_data) < total_size:
        chunk = sock.recv(min(8192, total_size - len(received_data)))
        if not chunk:
            raise ConnectionError("Соединение прервано")
        received_data += chunk

    sock.settimeout(None)
    print(f"[RECV] Получено {len(received_data)} байт")
    return received_data.decode('utf-8')


def send_large_data(sock, data):
    import time
    CHUNK_SIZE = 8192
    data_bytes = data.encode('utf-8')
    total_size = len(data_bytes)

    sock.send(f"SIZE:{total_size}\n".encode('utf-8'))
    time.sleep(0.1)

    sent = 0
    while sent < total_size:
        chunk = data_bytes[sent:sent + CHUNK_SIZE]
        sock.send(chunk)
        sent += len(chunk)
        time.sleep(0.01)
    print(f"[SEND] Отправлено {sent} байт")

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