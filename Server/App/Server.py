import socket
import threading
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import time
import os

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

# Путь к CSV относительно папки Server/App
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, "../../data/fruit_vegetable_classification_dataset.csv")
csv_file_path = os.path.normpath(csv_file_path)
current_csv_data = None

# ===================================== CSV =====================================
def load_initial_csv():
    global current_csv_data
    df = pd.read_csv(csv_file_path)
    current_csv_data = df.to_csv(index=False)
    print(f"[CSV] Загружен исходный файл ({len(current_csv_data)} байт)")

# ===================================== Работа с клиентами =====================================
def handle_client(conn, addr):
    try:
        # Увеличиваем таймаут для первого подключения
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
        
        # УБИРАЕМ таймаут после подключения
        conn.settimeout(None)
        
        update_client_list()
        print(f"[+] Клиент подключён: {name} (Lvl {level}, {mode}) — {addr}")

        # Просто держим соединение открытым, НЕ читаем данные
        # Клиент будет получать команды через send_large_data и conn.send
        while True:
            time.sleep(1)  # Просто ждём

    except socket.timeout:
        print(f"[!] Таймаут подключения {addr}")
    except Exception as e:
        print(f"[!] Ошибка клиента {addr}: {e}")
    finally:
        # Отключаем только если клиента больше нет в списке
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

# ===================================== Отправка и получение больших данных =====================================
def send_large_data(sock, data):
    CHUNK_SIZE = 8192
    data_bytes = data.encode('utf-8')
    total_size = len(data_bytes)

    sock.send(f"SIZE:{total_size}\n".encode('utf-8'))
    import time
    time.sleep(0.1)

    sent = 0
    while sent < total_size:
        chunk = data_bytes[sent:sent + CHUNK_SIZE]
        sock.send(chunk)
        sent += len(chunk)
        time.sleep(0.01)
    print(f"[SEND] Отправлено {sent} байт")

def receive_large_data(sock, timeout=120):
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

# ===================================== Запуск работы клиентов =====================================
def request_work_from_clients():
    if not clients:
        messagebox.showinfo("Инфо", "Нет подключённых клиентов.")
        return

    sorted_clients = sorted(clients.items(), key=lambda item: item[1][2])
    modes = set(client[3] for client in clients.values())

    # ВАЖНО: Сначала выполняем последовательных клиентов, ПОТОМ параллельных
    has_sequential = "Последовательно" in modes
    has_parallel = "Параллельно" in modes
    
    def run_workflow():
        global current_csv_data
        
        # Шаг 1: Последовательные клиенты (если есть)
        if has_sequential:
            print("\n" + "="*70)
            print("[ЭТАП 1] Запуск последовательных клиентов...")
            print("="*70)
            run_sequential(sorted_clients)
            print("\n" + "="*70)
            print("[ЭТАП 1] ✅ Последовательные клиенты завершены!")
            print("="*70 + "\n")
        
        # Шаг 2: Параллельные клиенты (если есть)
        if has_parallel:
            print("\n" + "="*70)
            print("[ЭТАП 2] Запуск параллельных клиентов...")
            print("="*70)
            run_parallel(sorted_clients)
            print("\n" + "="*70)
            print("[ЭТАП 2] ✅ Параллельные клиенты завершены!")
            print("="*70 + "\n")
        
        # Шаг 3: Сохранение финального результата
        if current_csv_data:
            import pandas as pd
            import io
            from datetime import datetime
            
            try:
                df = pd.read_csv(io.StringIO(current_csv_data))
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"final_processed_data_{timestamp}.csv"
                df.to_csv(output_path, index=False)
                
                print("\n" + "="*70)
                print("🎉 ВСЯ ОБРАБОТКА ЗАВЕРШЕНА!")
                print("="*70)
                print(f"✅ Финальный файл сохранён: {output_path}")
                print(f"📊 Всего строк: {len(df):,}")
                print(f"📊 Всего колонок: {len(df.columns)}")
                print(f"📋 Колонки: {', '.join(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}")
                print("="*70 + "\n")
                
            except Exception as e:
                print(f"[!] Ошибка сохранения финального файла: {e}")
                import traceback
                traceback.print_exc()
    
    # Запускаем в отдельном потоке
    threading.Thread(target=run_workflow, daemon=True).start()

def run_sequential(sorted_clients):
    global current_csv_data
    print("[РЕЖИМ] Последовательно")
    if current_csv_data is None:
        load_initial_csv()

    last_client_name = None
    
    for addr, (conn, name, level, mode) in sorted_clients:
        if mode != "Последовательно":
            continue
        if addr not in clients:
            print(f"[!] Клиент {name} отключён, пропускаем")
            continue
            
        try:
            print(f"\n[→] Отправка данных клиенту {name} (Lvl {level})")
            
            # ВАЖНО: временно устанавливаем таймаут только для операций
            conn.settimeout(180)  # 3 минуты на всю операцию
            
            send_large_data(conn, f"CSV_DATA:{current_csv_data}")
            time.sleep(0.5)
            
            conn.send("WORK".encode('utf-8'))
            
            result = conn.recv(4096).decode('utf-8')
            print(f"[✓] {name}: {result}")
            
            csv_update = receive_large_data(conn, timeout=180)
            
            if csv_update.startswith("CSV_UPDATED:"):
                current_csv_data = csv_update.replace("CSV_UPDATED:", "").strip()
                last_client_name = name
                print(f"[✓] Обновлённые данные получены от {name}")
            elif csv_update == "NO_UPDATE":
                print(f"[!] {name} не обновил данные")
            
            # ВАЖНО: убираем таймаут после завершения операции
            conn.settimeout(None)
            
        except socket.timeout:
            print(f"[!] Таймаут при работе с клиентом {name} - клиент остаётся подключённым")
            try:
                conn.settimeout(None)  # Сбрасываем таймаут
            except:
                pass
        except Exception as e:
            print(f"[!] Ошибка при работе с клиентом {name}: {e} - клиент остаётся подключённым")
            try:
                conn.settimeout(None)  # Сбрасываем таймаут
            except:
                pass
    
    # Сохраняем промежуточный результат после последовательных клиентов
    if current_csv_data and last_client_name:
        import pandas as pd
        import io
        
        try:
            df = pd.read_csv(io.StringIO(current_csv_data))
            print(f"\n[✓✓✓] Последовательная обработка завершена!")
            print(f"[INFO] Обработано строк: {len(df)}, Колонок: {len(df.columns)}")
            print(f"[INFO] Последний обработчик: {last_client_name}")
            
            # Проверяем наличие model_target (должен быть от Lemmatizer)
            if 'model_target' in df.columns:
                model1_count = len(df[df['model_target'] == 'model1'])
                model2_count = len(df[df['model_target'] == 'model2'])
                print(f"[INFO] Данные разделены: Model1={model1_count}, Model2={model2_count}")
                print(f"[✓] Данные готовы для параллельных клиентов!\n")
            else:
                print(f"[!] ВНИМАНИЕ: Колонка 'model_target' не найдена!")
                
        except Exception as e:
            print(f"[!] Ошибка проверки данных: {e}")
            
def run_parallel(sorted_clients):
    global current_csv_data
    print("[РЕЖИМ] Параллельно")
    
    if current_csv_data is None:
        print("[!] ОШИБКА: CSV данные не загружены!")
        return
    
    threads = []
    for addr, (conn, name, level, mode) in sorted_clients:
        if mode != "Параллельно":
            continue
        if addr not in clients:
            print(f"[!] Клиент {name} отключён, пропускаем")
            continue
            
        # Запускаем каждого клиента в отдельном потоке
        t = threading.Thread(
            target=process_parallel_client, 
            args=(conn, name, level, addr), 
            daemon=True
        )
        threads.append(t)
        t.start()
    
    # Ждём завершения всех параллельных клиентов
    for t in threads:
        t.join()

def process_parallel_client(conn, name, level, addr):
    """Обработка одного параллельного клиента"""
    global current_csv_data
    
    try:
        print(f"\n[→] Отправка данных клиенту {name} (Lvl {level})")
        
        # Устанавливаем таймаут для операций
        conn.settimeout(180)
        
        # Отправляем CSV данные
        send_large_data(conn, f"CSV_DATA:{current_csv_data}")
        time.sleep(0.5)
        
        # Отправляем команду WORK
        conn.send("WORK".encode('utf-8'))
        
        # Получаем результат
        result = conn.recv(4096).decode('utf-8')
        print(f"[✓] {name}: {result}")
        
        # Получаем обновлённые данные (если есть)
        csv_update = receive_large_data(conn, timeout=180)
        
        if csv_update.startswith("CSV_UPDATED:"):
            updated_csv = csv_update.replace("CSV_UPDATED:", "").strip()
            print(f"[✓] Получены обновлённые данные от {name} ({len(updated_csv)} байт)")
            
            # Сохраняем данные от параллельного клиента
            import pandas as pd
            import io
            from datetime import datetime
            
            df = pd.read_csv(io.StringIO(updated_csv))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"parallel_{name}_{timestamp}.csv"
            df.to_csv(output_path, index=False)
            print(f"[✓] Данные от {name} сохранены: {output_path}")
            
        elif csv_update == "NO_UPDATE":
            print(f"[!] {name} не вернул обновлённые данные")
        
        # Убираем таймаут
        conn.settimeout(None)
        
    except socket.timeout:
        print(f"[!] Таймаут при работе с {name}")
        try:
            conn.settimeout(None)
        except:
            pass
    except Exception as e:
        print(f"[!] Ошибка при работе с {name}: {e}")
        import traceback
        traceback.print_exc()
        try:
            conn.settimeout(None)
        except:
            pass

def send_work(conn, name, level):
    try:
        conn.send("WORK".encode('utf-8'))
        print(f"→ Отправлен запрос do_work() клиенту {name} (Lvl {level})")
    except:
        print(f"[!] Ошибка при отправке клиенту {name}")

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

    load_initial_csv()
    start_server()
    root.mainloop()

# ===================================== Main =====================================
if __name__ == "__main__":
    create_gui()
