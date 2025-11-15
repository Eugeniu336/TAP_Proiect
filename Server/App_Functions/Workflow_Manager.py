import threading
import time
import socket
import pandas as pd
import io
from datetime import datetime
from pathlib import Path

# Глобальные переменные для работы с данными
current_csv_data = None
current_csv_file = None

RECEIVED_DIR = Path("received_from_clients")
RECEIVED_DIR.mkdir(exist_ok=True)


class WorkflowManager:
    """Управление рабочим процессом обработки данных клиентами"""
    
    def __init__(self, clients_dict, send_file_func, receive_file_func, 
                 send_message_func, update_callback=None, results_callback=None):
        self.clients = clients_dict
        self.send_file = send_file_func
        self.receive_file = receive_file_func
        self.send_message = send_message_func
        self.update_callback = update_callback
        self.results_callback = results_callback
        
        global current_csv_data, current_csv_file
        self.csv_data = current_csv_data
        self.csv_file = current_csv_file
    
    def start_workflow(self):
        """Запуск полного рабочего процесса в отдельном потоке"""
        threading.Thread(target=self._run_workflow, daemon=True).start()
    
    def _run_workflow(self):
        """Основной рабочий процесс"""
        global current_csv_data, current_csv_file
        
        sorted_clients = sorted(self.clients.items(), key=lambda item: item[1][2])
        modes = set(client[3] for client in self.clients.values())
        
        has_sequential = "Последовательно" in modes
        has_parallel = "Параллельно" in modes
        
        # Шаг 1: Последовательные клиенты (БЕЗ Prediction_Client - уровень 8)
        if has_sequential:
            print("\n" + "="*70)
            print("[ЭТАП 1] Запуск последовательных клиентов...")
            print("="*70)
            self._run_sequential(sorted_clients, exclude_level=8)
            print("\n" + "="*70)
            print("[ЭТАП 1] ✅ Последовательные клиенты завершены!")
            print("="*70 + "\n")
        
        # Шаг 2: Параллельные клиенты
        if has_parallel:
            print("\n" + "="*70)
            print("[ЭТАП 2] Запуск параллельных клиентов...")
            print("="*70)
            self._run_parallel(sorted_clients)
            print("\n" + "="*70)
            print("[ЭТАП 2] ✅ Параллельные клиенты завершены!")
            print("="*70 + "\n")
        
        # Шаг 3: Prediction_Client (ПОСЛЕ обучения моделей - только уровень 8)
        if has_sequential:
            print("\n" + "="*70)
            print("[ЭТАП 3] Запуск Prediction Client...")
            print("="*70)
            self._run_sequential(sorted_clients, only_level=8)
            print("\n" + "="*70)
            print("[ЭТАП 3] ✅ Prediction Client завершен!")
            print("="*70 + "\n")
        
        # Шаг 4: Сохранение финального результата
        self._save_final_results()
    
    def _run_sequential(self, sorted_clients, exclude_level=None, only_level=None):
        """Последовательная обработка клиентами"""
        global current_csv_data, current_csv_file
        
        print("[РЕЖИМ] Последовательно")
        
        if current_csv_data is None:
            print("[!] ОШИБКА: CSV данные не загружены!")
            return
        
        last_client_name = None
        
        for addr, (conn, name, level, mode) in sorted_clients:
            if mode != "Последовательно":
                continue
            
            # Фильтрация по уровню
            if exclude_level is not None and level == exclude_level:
                continue
            if only_level is not None and level != only_level:
                continue
            
            if addr not in self.clients:
                print(f"[!] Клиент {name} отключён, пропускаем")
                continue
            
            try:
                print(f"\n[→] Отправка файла клиенту {name} (Lvl {level})")
                
                conn.settimeout(180)
                
                # Отправляем файл
                self.send_file(conn, current_csv_file)
                time.sleep(0.5)
                
                # Команда на работу
                conn.send("WORK".encode('utf-8'))
                
                # Получаем результат
                result = conn.recv(4096).decode('utf-8')
                print(f"[✓] {name}: {result}")
                
                # Получаем обработанный файл обратно
                header, data = self.receive_file(conn)
                
                if header and header.get("action") == "return_file":
                    filename = header.get("filename", "")
                    
                    # Проверяем, что это не NO_UPDATE
                    if filename != "no_update.txt" and len(data) > 100:
                        # Сохраняем обновленный CSV
                        with open(current_csv_file, 'wb') as f:
                            f.write(data)
                        
                        current_csv_data = data.decode('utf-8')
                        self.csv_data = current_csv_data
                        self.csv_file = current_csv_file
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
            self._verify_sequential_results(current_csv_data, last_client_name, only_level)
    
    def _verify_sequential_results(self, csv_data, last_client_name, only_level):
        """Проверка результатов последовательной обработки"""
        try:
            df = pd.read_csv(io.StringIO(csv_data))
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
    
    def _run_parallel(self, sorted_clients):
        """Параллельная обработка клиентами"""
        global current_csv_data, current_csv_file
        
        print("[РЕЖИМ] Параллельно")
        
        if current_csv_data is None:
            print("[!] ОШИБКА: CSV данные не загружены!")
            return
        
        threads = []
        for addr, (conn, name, level, mode) in sorted_clients:
            if mode != "Параллельно":
                continue
            if addr not in self.clients:
                print(f"[!] Клиент {name} отключён, пропускаем")
                continue
            
            t = threading.Thread(
                target=self._process_parallel_client,
                args=(conn, name, level, addr),
                daemon=True
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
    
    def _process_parallel_client(self, conn, name, level, addr):
        """Обработка одного параллельного клиента"""
        global current_csv_file
        
        try:
            print(f"\n[→] Отправка файла клиенту {name} (Lvl {level})")
            
            conn.settimeout(180)
            
            # Отправляем файл
            self.send_file(conn, current_csv_file)
            time.sleep(0.5)
            
            # Команда на работу
            conn.send("WORK".encode('utf-8'))
            
            # Получаем результат
            result = conn.recv(4096).decode('utf-8')
            print(f"[✓] {name}: {result}")
            
            # Получаем обработанный файл
            header, data = self.receive_file(conn)
            
            if header and header.get("action") == "return_file":
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
    
    def _save_final_results(self):
        """Сохранение финальных результатов обработки"""
        global current_csv_data, current_csv_file
        
        if not current_csv_data:
            print("[!] Нет данных для сохранения")
            return
        
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
            
            # Вызываем callback для отображения результатов
            if self.results_callback:
                # Небольшая задержка для завершения GUI операций
                if self.update_callback:
                    self.update_callback(500, self.results_callback)
                else:
                    self.results_callback()
        
        except Exception as e:
            print(f"[!] Ошибка сохранения финального файла: {e}")
            import traceback
            traceback.print_exc()


def set_csv_data(data, filepath):
    """Установка глобальных данных CSV для использования в workflow"""
    global current_csv_data, current_csv_file
    current_csv_data = data
    current_csv_file = filepath


def get_csv_data():
    """Получение текущих данных CSV"""
    global current_csv_data, current_csv_file
    return current_csv_data, current_csv_file