import socket
import threading
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import time
import os
import struct
import json
from pathlib import Path

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

# Путь к CSV относительно папки Server/App
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, "../../data/fruit_vegetable_classification_dataset.csv")
csv_file_path = os.path.normpath(csv_file_path)
current_csv_data = None
current_csv_file = "temp_processing.csv"

# ===================================== CSV =====================================
def load_initial_csv():
    global current_csv_data
    df = pd.read_csv(csv_file_path)
    current_csv_data = df.to_csv(index=False)
    # Сохраняем во временный файл
    with open(current_csv_file, 'w', encoding='utf-8') as f:
        f.write(current_csv_data)
    print(f"[CSV] Загружен исходный файл ({len(current_csv_data)} байт)")

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
    if not clients:
        messagebox.showinfo("Инфо", "Нет подключённых клиентов.")
        return

    sorted_clients = sorted(clients.items(), key=lambda item: item[1][2])
    modes = set(client[3] for client in clients.values())

    has_sequential = "Последовательно" in modes
    has_parallel = "Параллельно" in modes
    
    def run_workflow():
        global current_csv_data
        
        # Шаг 1: Последовательные клиенты (БЕЗ Prediction_Client!)
        if has_sequential:
            print("\n" + "="*70)
            print("[ЭТАП 1] Запуск последовательных клиентов...")
            print("="*70)
            run_sequential(sorted_clients, exclude_level=8)  # ← Исключаем уровень 8
            print("\n" + "="*70)
            print("[ЭТАП 1] ✅ Последовательные клиенты завершены!")
            print("="*70 + "\n")
        
        # Шаг 2: Параллельные клиенты
        if has_parallel:
            print("\n" + "="*70)
            print("[ЭТАП 2] Запуск параллельных клиентов...")
            print("="*70)
            run_parallel(sorted_clients)
            print("\n" + "="*70)
            print("[ЭТАП 2] ✅ Параллельные клиенты завершены!")
            print("="*70 + "\n")
        
        # Шаг 3: Prediction_Client (ПОСЛЕ обучения моделей)
        if has_sequential:
            print("\n" + "="*70)
            print("[ЭТАП 3] Запуск Prediction Client...")
            print("="*70)
            run_sequential(sorted_clients, only_level=8)  # ← Только уровень 8
            print("\n" + "="*70)
            print("[ЭТАП 3] ✅ Prediction Client завершен!")
            print("="*70 + "\n")
        
        # Шаг 4: Сохранение финального результата
        if current_csv_data:
            from datetime import datetime
            
            try:
                df = pd.read_csv(current_csv_file)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"final_processed_data_{timestamp}.csv"
                df.to_csv(output_path, index=False)
                
                print("\n" + "🎉" * 35)
                print("=" * 70)
                print("                 ВСЯ ОБРАБОТКА ЗАВЕРШЕНА!")
                print("=" * 70)
                print(f"\n📂 Финальный файл: {output_path}")
                print(f"📊 Всего записей: {len(df):,}")
                print(f"📋 Колонок: {len(df.columns)}")
                print("=" * 70 + "\n")
                
                root.after(500, show_results_window)
                
            except Exception as e:
                print(f"[!] Ошибка сохранения финального файла: {e}")
                import traceback
                traceback.print_exc()
    
    threading.Thread(target=run_workflow, daemon=True).start()

def run_sequential(sorted_clients, exclude_level=None, only_level=None):
    global current_csv_data, current_csv_file
    
    print("[РЕЖИМ] Последовательно")
    
    if current_csv_data is None:
        load_initial_csv()
    
    last_client_name = None
    
    for addr, (conn, name, level, mode) in sorted_clients:
        if mode != "Последовательно":
            continue
        
        # Фильтрация по уровню
        if exclude_level is not None and level == exclude_level:
            continue
        if only_level is not None and level != only_level:
            continue
            
        if addr not in clients:
            print(f"[!] Клиент {name} отключён, пропускаем")
            continue
            
        try:
            print(f"\n[→] Отправка файла клиенту {name} (Lvl {level})")
            
            conn.settimeout(180)
            
            # Отправляем файл
            send_file_to_client(conn, current_csv_file)
            time.sleep(0.5)
            
            # Команда на работу
            conn.send("WORK".encode('utf-8'))
            
            # Получаем результат
            result = conn.recv(4096).decode('utf-8')
            print(f"[✓] {name}: {result}")
            
            # Получаем обработанный файл обратно
            header, data = receive_file_from_client(conn)
            
            if header and header.get("action") == "return_file":
                filename = header.get("filename", "")
                
                # ВАЖНО: Проверяем, что это не NO_UPDATE
                if filename != "no_update.txt" and len(data) > 100:
                    # Сохраняем обновленный CSV
                    with open(current_csv_file, 'wb') as f:
                        f.write(data)
                    
                    current_csv_data = data.decode('utf-8')
                    last_client_name = name
                    print(f"[✓] Обновлённый файл получен от {name}")
                else:
                    print(f"[!] {name} не обновил данные (NO_UPDATE)")
            
            conn.settimeout(None)
            
        except socket.timeout:
            print(f"[!] Таймаут при работе с клиентом {name}")
            try:
                conn.settimeout(None)
            except:
                pass
        except Exception as e:
            print(f"[!] Ошибка при работе с клиентом {name}: {e}")
            import traceback
            traceback.print_exc()
            try:
                conn.settimeout(None)
            except:
                pass
    
    # Проверяем результат
    if current_csv_data and last_client_name:
        import io
        
        try:
            df = pd.read_csv(io.StringIO(current_csv_data))
            print(f"\n[✓✓✓] Последовательная обработка завершена!")
            print(f"[INFO] Обработано строк: {len(df)}, Колонок: {len(df.columns)}")
            print(f"[INFO] Последний обработчик: {last_client_name}")
            
            if 'model_target' in df.columns:
                model1_count = len(df[df['model_target'] == 'model1'])
                model2_count = len(df[df['model_target'] == 'model2'])
                print(f"[INFO] Данные разделены: Model1={model1_count}, Model2={model2_count}")
                print(f"[✓] Данные готовы для параллельных клиентов!\n")
            else:
                if only_level != 8:  # Не показываем предупреждение для Prediction
                    print(f"[!] ВНИМАНИЕ: Колонка 'model_target' не найдена!")
                
        except Exception as e:
            print(f"[!] Ошибка проверки данных: {e}")
            
def run_parallel(sorted_clients):
    global current_csv_data, current_csv_file
    
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
            
        t = threading.Thread(
            target=process_parallel_client, 
            args=(conn, name, level, addr), 
            daemon=True
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()

def process_parallel_client(conn, name, level, addr):
    """Обработка одного параллельного клиента"""
    global current_csv_file
    
    try:
        print(f"\n[→] Отправка файла клиенту {name} (Lvl {level})")
        
        conn.settimeout(180)
        
        # Отправляем файл
        send_file_to_client(conn, current_csv_file)
        time.sleep(0.5)
        
        # Команда на работу
        conn.send("WORK".encode('utf-8'))
        
        # Получаем результат
        result = conn.recv(4096).decode('utf-8')
        print(f"[✓] {name}: {result}")
        
        # Получаем обработанный файл
        header, data = receive_file_from_client(conn)
        
        if header and header.get("action") == "return_file":
            from datetime import datetime
            
            filename = header.get("filename", "processed.csv")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = RECEIVED_DIR / f"parallel_{name}_{timestamp}.csv"
            
            with open(save_path, 'wb') as f:
                f.write(data)
            
            print(f"[✓] Данные от {name} сохранены: {save_path}")
        
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

# ===================================== Окно результатов =====================================
def show_results_window():
    """Интерактивное окно с результатами и возможностью делать предсказания"""
    from datetime import datetime
    import io
    import pickle
    import os
    
    if not current_csv_data:
        messagebox.showinfo("Инфо", "Нет данных для отображения")
        return
    
    try:
        df = pd.read_csv(io.StringIO(current_csv_data))
        
        # Загружаем обученные модели
        model1_data = None
        model2_data = None
        
        if os.path.exists('model1_trained.pkl'):
            with open('model1_trained.pkl', 'rb') as f:
                model1_data = pickle.load(f)
        
        if os.path.exists('model2_trained.pkl'):
            with open('model2_trained.pkl', 'rb') as f:
                model2_data = pickle.load(f)
        
        # Создаём главное окно
        results_window = tk.Toplevel()
        results_window.title("🤖 AI Models Dashboard")
        results_window.geometry("900x700")
        
        # Notebook для вкладок
        from tkinter import ttk
        notebook = ttk.Notebook(results_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ==================== ВКЛАДКА 1: Статистика моделей ====================
        stats_frame = tk.Frame(notebook)
        notebook.add(stats_frame, text="📊 Статистика")
        
        stats_scroll = tk.Scrollbar(stats_frame)
        stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        stats_text = tk.Text(stats_frame, wrap=tk.WORD, yscrollcommand=stats_scroll.set,
                            font=("Courier", 10), bg="#f5f5f5")
        stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scroll.config(command=stats_text.yview)
        
        # Формируем статистику
        output = ""
        output += "=" * 80 + "\n"
        output += " " * 25 + "🎉 РЕЗУЛЬТАТЫ ОБУЧЕНИЯ 🎉\n"
        output += "=" * 80 + "\n\n"
        
        output += f"📂 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += f"📊 Всего записей: {len(df):,}\n"
        output += f"📋 Колонок: {len(df.columns)}\n\n"
        
        # Статистика предобработки
        output += "─" * 80 + "\n"
        output += "📝 ПРЕДОБРАБОТКА ДАННЫХ\n"
        output += "─" * 80 + "\n"
        
        if 'cleaned_text' in df.columns:
            output += f"✅ Text Cleaning: {df['cleaned_text'].notna().sum():,} записей\n"
        if 'tokens' in df.columns:
            output += f"✅ Tokenization: {df['tokens'].notna().sum():,} записей\n"
        if 'lemmas' in df.columns:
            output += f"✅ Lemmatization: {df['lemmas'].notna().sum():,} записей\n"
        
        if 'model_target' in df.columns:
            m1 = len(df[df['model_target'] == 'model1'])
            m2 = len(df[df['model_target'] == 'model2'])
            output += f"\n📊 Разделение данных:\n"
            output += f"   • Model 1 (Binary): {m1:,} ({m1/len(df)*100:.1f}%)\n"
            output += f"   • Model 2 (Multi-class): {m2:,} ({m2/len(df)*100:.1f}%)\n"
        
        output += "\n" + "─" * 80 + "\n"
        output += "🤖 МОДЕЛЬ 1: BINARY CLASSIFICATION (Decision Tree)\n"
        output += "─" * 80 + "\n"
        
        if model1_data:
            output += f"📈 Обучение:\n"
            output += f"   • Train Accuracy: {model1_data['train_acc']:.4f} ({model1_data['train_acc']*100:.2f}%)\n"
            output += f"   • Test Accuracy:  {model1_data['test_acc']:.4f} ({model1_data['test_acc']*100:.2f}%)\n"
            output += f"   • Train Size: {model1_data['train_size']:,} samples\n"
            output += f"   • Test Size:  {model1_data['test_size']:,} samples\n"
            output += f"   • Classes: {', '.join(model1_data['classes'])}\n"
            
            if 'model1_val_accuracy' in df.columns:
                val_acc = df['model1_val_accuracy'].iloc[0]
                cv_mean = df.get('model1_cv_mean', pd.Series([0])).iloc[0]
                output += f"\n📊 Валидация:\n"
                output += f"   • Validation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)\n"
                output += f"   • Cross-Validation: {cv_mean:.4f} ({cv_mean*100:.2f}%)\n"
        else:
            output += "❌ Модель не обучена\n"
        
        output += "\n" + "─" * 80 + "\n"
        output += "🤖 МОДЕЛЬ 2: MULTI-CLASS CLASSIFICATION (Random Forest)\n"
        output += "─" * 80 + "\n"
        
        if model2_data:
            output += f"📈 Обучение:\n"
            output += f"   • Train Accuracy: {model2_data['train_acc']:.4f} ({model2_data['train_acc']*100:.2f}%)\n"
            output += f"   • Test Accuracy:  {model2_data['test_acc']:.4f} ({model2_data['test_acc']*100:.2f}%)\n"
            output += f"   • Train Size: {model2_data['train_size']:,} samples\n"
            output += f"   • Test Size:  {model2_data['test_size']:,} samples\n"
            output += f"   • Number of Classes: {model2_data['n_classes']}\n"
            
            if 'feature_importance' in model2_data:
                top_features = sorted(model2_data['feature_importance'].items(), 
                                    key=lambda x: x[1], reverse=True)[:5]
                output += f"\n📊 Top 5 Features:\n"
                for feat, imp in top_features:
                    output += f"   • {feat}: {imp:.4f}\n"
            
            if 'model2_val_accuracy' in df.columns:
                val_acc = df['model2_val_accuracy'].iloc[0]
                cv_mean = df.get('model2_cv_mean', pd.Series([0])).iloc[0]
                output += f"\n📊 Валидация:\n"
                output += f"   • Validation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)\n"
                output += f"   • Cross-Validation: {cv_mean:.4f} ({cv_mean*100:.2f}%)\n"
        else:
            output += "❌ Модель не обучена\n"
        
        output += "\n" + "=" * 80 + "\n"
        output += " " * 20 + "✨ МОДЕЛИ ГОТОВЫ К ИСПОЛЬЗОВАНИЮ ✨\n"
        output += "=" * 80 + "\n"
        
        stats_text.insert("1.0", output)
        stats_text.config(state=tk.DISABLED)
        
        # ==================== ВКЛАДКА 2: Интерактивные предсказания ====================
        predict_frame = tk.Frame(notebook, bg="#f0f0f0")
        notebook.add(predict_frame, text="🔮 Предсказания")
        
        # Заголовок
        title_frame = tk.Frame(predict_frame, bg="#4CAF50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🔮 Тестирование моделей", 
                font=("Arial", 16, "bold"), bg="#4CAF50", fg="white").pack(pady=15)
        
        # Форма ввода
        input_frame = tk.Frame(predict_frame, bg="#f0f0f0")
        input_frame.pack(pady=20, padx=20, fill=tk.BOTH)
        
        # Получаем уникальные значения из датасета
        unique_shapes = df['shape'].unique().tolist() if 'shape' in df.columns else []
        unique_colors = df['color'].unique().tolist() if 'color' in df.columns else []
        unique_tastes = df['taste'].unique().tolist() if 'taste' in df.columns else []
        
        # Поля ввода
        fields = []
        
        row = 0
        tk.Label(input_frame, text="Размер (см):", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
        size_entry = tk.Entry(input_frame, font=("Arial", 11), width=20)
        size_entry.insert(0, "5.0")
        size_entry.grid(row=row, column=1, pady=8, padx=10)
        fields.append(("size", size_entry))
        
        row += 1
        tk.Label(input_frame, text="Вес (г):", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
        weight_entry = tk.Entry(input_frame, font=("Arial", 11), width=20)
        weight_entry.insert(0, "150")
        weight_entry.grid(row=row, column=1, pady=8, padx=10)
        fields.append(("weight", weight_entry))
        
        row += 1
        tk.Label(input_frame, text="Цена (₹):", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
        price_entry = tk.Entry(input_frame, font=("Arial", 11), width=20)
        price_entry.insert(0, "50")
        price_entry.grid(row=row, column=1, pady=8, padx=10)
        fields.append(("price", price_entry))
        
        row += 1
        tk.Label(input_frame, text="Форма:", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
        from tkinter import ttk
        shape_var = tk.StringVar(value=unique_shapes[0] if unique_shapes else "round")
        shape_combo = ttk.Combobox(input_frame, textvariable=shape_var, values=unique_shapes, 
                                   font=("Arial", 11), width=18, state="readonly")
        shape_combo.grid(row=row, column=1, pady=8, padx=10)
        fields.append(("shape", shape_var))
        
        row += 1
        tk.Label(input_frame, text="Цвет:", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
        color_var = tk.StringVar(value=unique_colors[0] if unique_colors else "red")
        color_combo = ttk.Combobox(input_frame, textvariable=color_var, values=unique_colors,
                                   font=("Arial", 11), width=18, state="readonly")
        color_combo.grid(row=row, column=1, pady=8, padx=10)
        fields.append(("color", color_var))
        
        row += 1
        tk.Label(input_frame, text="Вкус:", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
        taste_var = tk.StringVar(value=unique_tastes[0] if unique_tastes else "sweet")
        taste_combo = ttk.Combobox(input_frame, textvariable=taste_var, values=unique_tastes,
                                   font=("Arial", 11), width=18, state="readonly")
        taste_combo.grid(row=row, column=1, pady=8, padx=10)
        fields.append(("taste", taste_var))
        
        # Результат
        result_frame = tk.Frame(predict_frame, bg="#ffffff", relief=tk.RIDGE, bd=2)
        result_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        result_text = tk.Text(result_frame, wrap=tk.WORD, font=("Courier", 11), 
                             bg="#ffffff", height=12)
        result_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        def make_prediction():
            """Функция предсказания"""
            if not model1_data or not model2_data:
                result_text.delete("1.0", tk.END)
                result_text.insert("1.0", "❌ Модели не обучены! Сначала запустите обучение.")
                return
            
            try:
                import numpy as np
                import pandas as pd
                
                # Получаем данные из полей
                size = float(size_entry.get())
                weight = float(weight_entry.get())
                price = float(price_entry.get())
                shape = shape_var.get()
                color = color_var.get()
                taste = taste_var.get()
                
                # === ПРЕДСКАЗАНИЕ MODEL 1 (Binary) ===
                X1_data = {
                    'size (cm)': [size],
                    'weight (g)': [weight],
                    'avg_price (₹)': [price]
                }
                
                # Кодируем категориальные признаки для Model1
                for col in ['shape', 'color', 'taste']:
                    le = model1_data['le_dict'][col]
                    val = {'shape': shape, 'color': color, 'taste': taste}[col]
                    if val in le.classes_:
                        encoded = le.transform([val])[0]
                    else:
                        encoded = 0
                    X1_data[f'{col}_encoded'] = [encoded]
                
                # Создаём DataFrame с правильными именами колонок
                X1_sample = pd.DataFrame(X1_data)
                X1_sample = X1_sample[model1_data['feature_cols']]  # Правильный порядок колонок
                
                pred1_encoded = model1_data['model'].predict(X1_sample)[0]
                pred1_label = model1_data['le_target'].inverse_transform([pred1_encoded])[0]
                pred1_proba = model1_data['model'].predict_proba(X1_sample)[0]
                
                # === ПРЕДСКАЗАНИЕ MODEL 2 (Multi-class) ===
                X2_data = {
                    'size (cm)': [size],
                    'weight (g)': [weight],
                    'avg_price (₹)': [price]
                }
                
                for col in ['shape', 'color', 'taste', 'type']:
                    le = model2_data['le_dict'][col]
                    if col == 'type':
                        val = pred1_label  # Используем предсказание Model1
                    else:
                        val = {'shape': shape, 'color': color, 'taste': taste}[col]
                    
                    if val in le.classes_:
                        encoded = le.transform([val])[0]
                    else:
                        encoded = 0
                    X2_data[f'{col}_encoded'] = [encoded]
                
                # Создаём DataFrame с правильными именами колонок
                X2_sample = pd.DataFrame(X2_data)
                X2_sample = X2_sample[model2_data['feature_cols']]  # Правильный порядок колонок
                
                pred2_encoded = model2_data['model'].predict(X2_sample)[0]
                pred2_label = model2_data['le_target'].inverse_transform([pred2_encoded])[0]
                pred2_proba = model2_data['model'].predict_proba(X2_sample)[0]
                
                # Топ-3 предсказания для Model2
                top3_indices = np.argsort(pred2_proba)[-3:][::-1]
                top3_labels = model2_data['le_target'].inverse_transform(top3_indices)
                top3_probas = pred2_proba[top3_indices]
                
                # Формируем результат (остальное без изменений)
                result = ""
                result += "=" * 70 + "\n"
                result += "                    🔮 РЕЗУЛЬТАТ ПРЕДСКАЗАНИЯ\n"
                result += "=" * 70 + "\n\n"
                
                result += "📝 Входные данные:\n"
                result += f"   • Размер: {size} см\n"
                result += f"   • Вес: {weight} г\n"
                result += f"   • Цена: {price} ₹\n"
                result += f"   • Форма: {shape}\n"
                result += f"   • Цвет: {color}\n"
                result += f"   • Вкус: {taste}\n"
                
                result += "\n" + "─" * 70 + "\n"
                result += "🤖 MODEL 1: Binary Classification\n"
                result += "─" * 70 + "\n"
                result += f"   Тип: {pred1_label.upper()}\n"
                result += f"   Уверенность: {max(pred1_proba)*100:.2f}%\n"
                result += f"\n   Распределение вероятностей:\n"
                for i, cls in enumerate(model1_data['le_target'].classes_):
                    bar_len = int(pred1_proba[i] * 40)
                    bar = "█" * bar_len + "░" * (40 - bar_len)
                    result += f"   {cls:12s} [{bar}] {pred1_proba[i]*100:5.2f}%\n"
                
                result += "\n" + "─" * 70 + "\n"
                result += "🤖 MODEL 2: Multi-class Classification\n"
                result += "─" * 70 + "\n"
                result += f"   Название: {pred2_label.upper()}\n"
                result += f"   Уверенность: {max(pred2_proba)*100:.2f}%\n"
                result += f"\n   Топ-3 предсказания:\n"
                for i, (label, proba) in enumerate(zip(top3_labels, top3_probas), 1):
                    bar_len = int(proba * 40)
                    bar = "█" * bar_len + "░" * (40 - bar_len)
                    result += f"   {i}. {label:15s} [{bar}] {proba*100:5.2f}%\n"
                
                result += "\n" + "=" * 70 + "\n"
                result += f"                    ✅ Итог: {pred2_label.upper()}\n"
                result += "=" * 70 + "\n"
                
                result_text.delete("1.0", tk.END)
                result_text.insert("1.0", result)
                
            except Exception as e:
                result_text.delete("1.0", tk.END)
                result_text.insert("1.0", f"❌ Ошибка при предсказании:\n{str(e)}")
                import traceback
                traceback.print_exc()
        
        # Кнопка предсказания
        btn_frame = tk.Frame(predict_frame, bg="#f0f0f0")
        btn_frame.pack(pady=10)
        
        predict_btn = tk.Button(btn_frame, text="🔮 Сделать предсказание", 
                               command=make_prediction,
                               font=("Arial", 12, "bold"), 
                               bg="#4CAF50", fg="white",
                               width=25, height=2,
                               cursor="hand2")
        predict_btn.pack()
        
        # ==================== ВКЛАДКА 3: История предсказаний ====================
        if os.path.exists('predictions_results.json'):
            history_frame = tk.Frame(notebook)
            notebook.add(history_frame, text="📜 История")
            
            history_scroll = tk.Scrollbar(history_frame)
            history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            history_text = tk.Text(history_frame, wrap=tk.WORD, 
                                  yscrollcommand=history_scroll.set,
                                  font=("Courier", 10), bg="#f5f5f5")
            history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            history_scroll.config(command=history_text.yview)
            
            with open('predictions_results.json', 'r') as f:
                predictions = json.load(f)
            
            history_output = ""
            history_output += "=" * 80 + "\n"
            history_output += " " * 25 + "📜 ИСТОРИЯ ПРЕДСКАЗАНИЙ\n"
            history_output += "=" * 80 + "\n\n"
            history_output += f"Всего предсказаний: {len(predictions)}\n\n"
            
            for i, pred in enumerate(predictions[:20], 1):  # Показываем первые 20
                history_output += f"─── Предсказание #{i} {'─' * 60}\n"
                inp = pred['input']
                history_output += f"Input: {inp['color']} {inp['shape']}, {inp['size']} см, {inp['weight']} г\n"
                
                m1 = pred['predictions']['model1']
                history_output += f"Model1: {m1['type']} ({m1['confidence']*100:.1f}%)\n"
                
                m2 = pred['predictions']['model2']
                history_output += f"Model2: {m2['name']} ({m2['confidence']*100:.1f}%)\n"
                
                if 'actual' in pred:
                    history_output += f"Actual: {pred['actual']['name']}"
                    if pred.get('correct', {}).get('model2'):
                        history_output += " ✅\n"
                    else:
                        history_output += " ❌\n"
                
                history_output += "\n"
            
            history_text.insert("1.0", history_output)
            history_text.config(state=tk.DISABLED)
        
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось отобразить результаты:\n{e}")
        import traceback
        traceback.print_exc()

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

    load_initial_csv()
    start_server()
    root.mainloop()

# ===================================== Main =====================================
if __name__ == "__main__":
    create_gui()