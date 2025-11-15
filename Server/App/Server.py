import socket
import threading
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import time
import os
import struct
import json
import sys
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
            raise ConnectionError("Соединение закрыто клиентом")
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
        print(f"[!] Файл не найден: {filepath}")
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
    print(f"[-->] Отправлен файл {filename} ({len(data)} байт)")
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
            conn.send("ERROR: Имя уже используется".encode('utf-8'))
            conn.close()
            return

        clients[addr] = (conn, name, int(level), mode)
        names.add(name)
        conn.send("CONNECTED".encode('utf-8'))
        
        conn.settimeout(None)
        
        update_client_list()
        print(f"[+] Клиент подключён: {name} (Lvl {level}, {mode}) — {addr}")

        # Держим соединение открытым
        while True:
            time.sleep(1)

    except socket.timeout:
        print(f"[!] Таймаут подключения {addr}")
    except Exception as e:
        print(f"[!] Ошибка клиента {addr}: {e}")
    finally:
        if addr in clients:
            disconnect_client(addr, silent=True)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[СЕРВЕР ЗАПУЩЕН] {HOST}:{PORT}")
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
        print(f"[-] Клиент отключён: {name}")
    update_client_list()

def disconnect_all():
    for addr in list(clients.keys()):
        disconnect_client(addr, silent=True)
    update_client_list()

# ===================================== Запуск работы клиентов =====================================
def request_work_from_clients():
    """Запуск рабочего процесса через WorkflowManager"""
    if not clients:
        messagebox.showinfo("Инфо", "Нет подключённых клиентов.")
        return
    
    # Создаём WorkflowManager с callback'ами
    workflow = WorkflowManager(
        clients_dict=clients,
        send_file_func=send_file_to_client,
        receive_file_func=receive_file_from_client,
        send_message_func=send_message,
        update_callback=lambda delay, func: root.after(delay, func),
        results_callback=show_results_window
    )
    
    # Запускаем workflow
    workflow.start_workflow()

# ===================================== GUI =====================================
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
    global client_list, root
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
    tk.Button(btn_frame, text="📊 Показать результаты", command=show_results_window, bg="#87ceeb").pack(side=tk.LEFT, padx=5)

    # Загрузка начальных CSV данных
    csv_data, csv_file = load_initial_csv()
    if csv_data and csv_file:
        set_csv_data(csv_data, csv_file)
    
    start_server()
    root.mainloop()

# ===================================== Main =====================================
if __name__ == "__main__":
    create_gui()