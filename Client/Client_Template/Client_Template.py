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


def do_work():
    work = "Результат работы клиента"
    """
    Заглушка для реальной задачи.
    (づ｡◕‿‿◕｡)づ 
    """
    return work


def listen_server():
    global connected
    while connected:
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if msg == "DISCONNECT":
                messagebox.showinfo("Сервер", "Вы были отключены сервером.")
                disconnect()
                break
            elif msg.startswith("ERROR:"):
                messagebox.showerror("Ошибка", msg.replace("ERROR:", "").strip())
                disconnect()
                break
            elif msg:
                print(f"[Сервер] -> {msg}")
                result = do_work()
                client_socket.send(result.encode('utf-8'))
        except:
            break


def connect():
    global client_socket, connected, SERVER_IP, PORT
    if connected:
        return
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, PORT))
        data = f"{CLIENT_NAME}|{CLIENT_LEVEL}|{CLIENT_MODE}"
        client_socket.send(data.encode('utf-8'))

        # Проверим сразу ответ
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
    except:
        messagebox.showerror("Ошибка", f"Не удалось подключиться к серверу {SERVER_IP}:{PORT}.")


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
        # ✅ добавили глобальные переменные!
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
