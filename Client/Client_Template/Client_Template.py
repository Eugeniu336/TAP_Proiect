import socket
import threading
import tkinter as tk
from tkinter import messagebox

SERVER_IP = socket.gethostbyname(socket.gethostname())
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
    global client_socket, connected
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
        status_label.config(text="Подключен", fg="green")
    except:
        messagebox.showerror("Ошибка", "Не удалось подключиться к серверу.")


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


# ============================================= GUI =============================================
def create_gui():
    global status_label
    root = tk.Tk()
    root.title(f"Клиент — {CLIENT_NAME}")

    tk.Label(root, text=f"Имя: {CLIENT_NAME}", font=("Arial", 12)).pack(pady=5)
    tk.Label(root, text=f"Уровень: {CLIENT_LEVEL}, Режим: {CLIENT_MODE}", font=("Arial", 10)).pack(pady=2)

    status_label = tk.Label(root, text="Отключен", fg="red", font=("Arial", 12))
    status_label.pack(pady=5)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Подключиться", command=connect).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Отключиться", command=disconnect).pack(side=tk.LEFT, padx=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
