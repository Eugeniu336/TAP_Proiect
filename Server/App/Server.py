import socket
import threading
import tkinter as tk
from tkinter import messagebox

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

# =========================================== Основная логика ===========================================
def handle_client(conn, addr):
    try:
        data = conn.recv(1024).decode('utf-8')
        name, level, mode = data.split('|')

        if name in names:
            conn.send("ERROR: Имя уже используется".encode('utf-8'))
            conn.close()
            return

        clients[addr] = (conn, name, int(level), mode)
        names.add(name)
        update_client_list()
        print(f"[+] Клиент подключён: {name} (Lvl {level}, {mode}) — {addr}")

        while True:
            msg = conn.recv(1024).decode('utf-8')
            if not msg:
                break
            print(f"[{name}] -> {msg}")
    except Exception as e:
        print(f"[!] Ошибка клиента {addr}: {e}")
    finally:
        disconnect_client(addr, silent=True)


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[СЕРВЕР ЗАПУЩЕН] {HOST}:{PORT}")
    threading.Thread(target=accept_clients, args=(server,), daemon=True).start()


def accept_clients(server):
    while server_running:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


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
        print(f"[-] Клиент отключён: {name}")
    update_client_list()


def disconnect_all():
    for addr in list(clients.keys()):
        disconnect_client(addr, silent=True)
    update_client_list()


# =========================================== Новая логика работы ===========================================
def request_work_from_clients():
    if not clients:
        messagebox.showinfo("Инфо", "Нет подключённых клиентов.")
        return

    # Сортируем клиентов по уровню (Level)
    sorted_clients = sorted(clients.items(), key=lambda item: item[1][2])

    # Собираем все режимы (mode)
    modes = set(client[3] for client in clients.values())

    # Запускаем нужный режим
    if "Параллельно" in modes:
        threading.Thread(target=run_parallel, args=(sorted_clients,), daemon=True).start()
    if "Последовательно" in modes:
        threading.Thread(target=run_sequential, args=(sorted_clients,), daemon=True).start()


def run_sequential(sorted_clients):
    # Отправляет запросы do_work() по уровням — один за другим.
    print("[РЕЖИМ] Последовательно")
    for addr, (conn, name, level, mode) in sorted_clients:
        if mode != "Последовательно":
            continue
        try:
            conn.send("WORK".encode('utf-8'))
            print(f"→ Отправлен запрос do_work() клиенту {name} (Lvl {level})")
        except:
            print(f"[!] Ошибка при отправке клиенту {name}")


def run_parallel(sorted_clients):
    # Отправляет запросы do_work() одновременно.
    print("[РЕЖИМ] Параллельно")
    threads = []
    for addr, (conn, name, level, mode) in sorted_clients:
        if mode != "Параллельно":
            continue
        t = threading.Thread(target=lambda: send_work(conn, name, level), daemon=True)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


def send_work(conn, name, level):
    try:
        conn.send("WORK".encode('utf-8'))
        print(f"→ Отправлен запрос do_work() клиенту {name} (Lvl {level})")
    except:
        print(f"[!] Ошибка при отправке клиенту {name}")


# ============================================= GUI =============================================
def update_client_list():
    client_list.delete(0, tk.END)
    for addr, (_, name, level, mode) in clients.items():
        client_list.insert(tk.END, f"{name} (Lvl {level}, {mode}) — {addr[0]}")


def on_disconnect_one():
    selection = client_list.curselection()
    if not selection:
        messagebox.showinfo("Инфо", "Выберите клиента для отключения.")
        return
    addr = list(clients.keys())[selection[0]]
    disconnect_client(addr)


def create_gui():
    global client_list
    root = tk.Tk()
    root.title("Сервер управления клиентами")

    tk.Label(root, text=f"Сервер: {HOST}:{PORT}", font=("Arial", 12)).pack(pady=5)

    client_list = tk.Listbox(root, width=50, height=10)
    client_list.pack(padx=10, pady=5)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Отключить выбранного", command=on_disconnect_one).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Отключить всех", command=disconnect_all).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="▶ Запросить do_work()", command=request_work_from_clients, bg="#90ee90").pack(side=tk.LEFT, padx=5)

    start_server()
    root.mainloop()


if __name__ == "__main__":
    create_gui()
