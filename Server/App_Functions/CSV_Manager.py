import pandas as pd
import os
from pathlib import Path

# ===================================== Пути и конфигурация =====================================
# Путь к CSV относительно папки Server/App
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, "../../data/fruit_vegetable_classification_dataset.csv")
csv_file_path = os.path.normpath(csv_file_path)

# Глобальные переменные для хранения данных
current_csv_data = None
current_csv_file = "temp_processing.csv"

# ===================================== Основные функции =====================================

def load_initial_csv():
    """
    Загрузка исходного CSV файла из датасета.
    
    Загружает данные из файла, сохраняет в памяти и создает временный файл
    для последующей обработки клиентами.
    
    Returns:
        tuple: (csv_data: str, csv_file: str) - данные и путь к файлу
               или (None, None) в случае ошибки
    
    Raises:
        FileNotFoundError: Если CSV файл не найден
        pd.errors.EmptyDataError: Если файл пустой
    """
    global current_csv_data
    
    try:
        # Проверяем существование файла
        if not os.path.exists(csv_file_path):
            print(f"[CSV ERROR] Файл не найден: {csv_file_path}")
            return None, None
        
        # Загружаем CSV
        df = pd.read_csv(csv_file_path)
        
        # Проверяем, что данные загружены
        if df.empty:
            print(f"[CSV ERROR] Файл пустой: {csv_file_path}")
            return None, None
        
        # Сохраняем в памяти
        current_csv_data = df.to_csv(index=False)
        
        # Сохраняем во временный файл для обработки
        with open(current_csv_file, 'w', encoding='utf-8') as f:
            f.write(current_csv_data)
        
        print(f"[CSV] ✅ Загружен исходный файл")
        print(f"[CSV] 📊 Размер: {len(current_csv_data):,} байт")
        print(f"[CSV] 📋 Строк: {len(df):,}")
        print(f"[CSV] 📁 Колонок: {len(df.columns)}")
        print(f"[CSV] 💾 Временный файл: {current_csv_file}")
        
        return current_csv_data, current_csv_file
        
    except FileNotFoundError:
        print(f"[CSV ERROR] Файл не найден: {csv_file_path}")
        print(f"[CSV ERROR] Убедитесь, что датасет находится по пути: {csv_file_path}")
        return None, None
    except pd.errors.EmptyDataError:
        print(f"[CSV ERROR] Файл пустой или поврежден: {csv_file_path}")
        return None, None
    except Exception as e:
        print(f"[CSV ERROR] Ошибка при загрузке CSV: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def get_current_csv_data():
    """
    Получить текущие CSV данные в виде строки.
    
    Returns:
        str: CSV данные в текстовом формате или None если данные не загружены
    """
    return current_csv_data

def get_current_csv_file():
    """
    Получить путь к текущему временному CSV файлу.
    
    Returns:
        str: Путь к временному файлу обработки
    """
    return current_csv_file

def set_current_csv_data(data):
    """
    Установить текущие CSV данные.
    
    Обновляет данные в памяти и записывает их во временный файл.
    
    Args:
        data (str or bytes): CSV данные в текстовом формате или байтах
    
    Returns:
        bool: True если обновление успешно, False в случае ошибки
    """
    global current_csv_data
    
    try:
        # Преобразуем bytes в строку если необходимо
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        # Обновляем данные в памяти
        current_csv_data = data
        
        # Сохраняем во временный файл
        with open(current_csv_file, 'w', encoding='utf-8') as f:
            f.write(current_csv_data)
        
        print(f"[CSV] 🔄 Данные обновлены ({len(current_csv_data):,} байт)")
        return True
        
    except Exception as e:
        print(f"[CSV ERROR] Ошибка при обновлении данных: {e}")
        import traceback
        traceback.print_exc()
        return False

def reload_csv_from_file():
    """
    Перезагрузить CSV данные из временного файла.
    
    Полезно если данные были изменены внешним процессом.
    
    Returns:
        bool: True если перезагрузка успешна, False в случае ошибки
    """
    global current_csv_data
    
    try:
        if not os.path.exists(current_csv_file):
            print(f"[CSV ERROR] Временный файл не найден: {current_csv_file}")
            return False
        
        with open(current_csv_file, 'r', encoding='utf-8') as f:
            current_csv_data = f.read()
        
        print(f"[CSV] 🔄 Данные перезагружены из {current_csv_file}")
        return True
        
    except Exception as e:
        print(f"[CSV ERROR] Ошибка при перезагрузке: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_csv_info():
    """
    Получить информацию о текущих CSV данных.
    
    Returns:
        dict: Словарь с информацией о данных или None если данные не загружены
        {
            'rows': int,
            'columns': int,
            'size_bytes': int,
            'columns_list': list,
            'file_path': str
        }
    """
    if current_csv_data is None:
        return None
    
    try:
        import io
        df = pd.read_csv(io.StringIO(current_csv_data))
        
        return {
            'rows': len(df),
            'columns': len(df.columns),
            'size_bytes': len(current_csv_data),
            'columns_list': df.columns.tolist(),
            'file_path': current_csv_file
        }
        
    except Exception as e:
        print(f"[CSV ERROR] Ошибка при получении информации: {e}")
        return None

def validate_csv_data():
    """
    Проверить корректность текущих CSV данных.
    
    Returns:
        tuple: (bool, str) - (валидность, сообщение об ошибке)
    """
    if current_csv_data is None:
        return False, "Данные не загружены"
    
    try:
        import io
        df = pd.read_csv(io.StringIO(current_csv_data))
        
        if df.empty:
            return False, "CSV данные пустые"
        
        if len(df.columns) == 0:
            return False, "Нет колонок в данных"
        
        return True, "Данные корректны"
        
    except Exception as e:
        return False, f"Ошибка валидации: {str(e)}"

def reset_to_initial():
    """
    Сбросить данные к исходному состоянию.
    
    Перезагружает данные из исходного файла датасета.
    
    Returns:
        tuple: (csv_data, csv_file) или (None, None) в случае ошибки
    """
    print("[CSV] 🔄 Сброс к исходному состоянию...")
    return load_initial_csv()

def backup_current_data(backup_name=None):
    """
    Создать резервную копию текущих данных.
    
    Args:
        backup_name (str, optional): Имя файла бэкапа. Если None, создается автоматически.
    
    Returns:
        str: Путь к файлу бэкапа или None в случае ошибки
    """
    if current_csv_data is None:
        print("[CSV ERROR] Нет данных для бэкапа")
        return None
    
    try:
        from datetime import datetime
        
        # Создаем папку для бэкапов
        backup_dir = Path("csv_backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Генерируем имя файла если не указано
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.csv"
        
        backup_path = backup_dir / backup_name
        
        # Сохраняем бэкап
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(current_csv_data)
        
        print(f"[CSV] 💾 Бэкап создан: {backup_path}")
        return str(backup_path)
        
    except Exception as e:
        print(f"[CSV ERROR] Ошибка при создании бэкапа: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_dataframe():
    """
    Получить текущие данные как pandas DataFrame.
    
    Returns:
        pd.DataFrame: DataFrame с данными или None в случае ошибки
    """
    if current_csv_data is None:
        return None
    
    try:
        import io
        return pd.read_csv(io.StringIO(current_csv_data))
    except Exception as e:
        print(f"[CSV ERROR] Ошибка при создании DataFrame: {e}")
        return None

def save_dataframe(df, update_current=True):
    """
    Сохранить DataFrame как текущие CSV данные.
    
    Args:
        df (pd.DataFrame): DataFrame для сохранения
        update_current (bool): Обновить ли текущие данные в памяти
    
    Returns:
        bool: True если сохранение успешно, False в случае ошибки
    """
    try:
        csv_string = df.to_csv(index=False)
        
        if update_current:
            return set_current_csv_data(csv_string)
        else:
            # Только сохраняем в файл без обновления в памяти
            with open(current_csv_file, 'w', encoding='utf-8') as f:
                f.write(csv_string)
            print(f"[CSV] 💾 DataFrame сохранен в {current_csv_file}")
            return True
            
    except Exception as e:
        print(f"[CSV ERROR] Ошибка при сохранении DataFrame: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_csv_path():
    """
    Получить путь к исходному CSV файлу датасета.
    
    Returns:
        str: Путь к исходному файлу
    """
    return csv_file_path

def cleanup_temp_files():
    """
    Удалить временные CSV файлы.
    
    Returns:
        bool: True если очистка успешна, False в случае ошибки
    """
    try:
        if os.path.exists(current_csv_file):
            os.remove(current_csv_file)
            print(f"[CSV] 🗑️ Временный файл удален: {current_csv_file}")
        return True
    except Exception as e:
        print(f"[CSV ERROR] Ошибка при удалении временных файлов: {e}")
        return False

# ===================================== Служебные функции =====================================

def _print_csv_stats():
    """Внутренняя функция для вывода статистики CSV данных"""
    info = get_csv_info()
    if info:
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА CSV ДАННЫХ")
        print("="*60)
        print(f"Строк:        {info['rows']:,}")
        print(f"Колонок:      {info['columns']}")
        print(f"Размер:       {info['size_bytes']:,} байт")
        print(f"Файл:         {info['file_path']}")
        print(f"Колонки:      {', '.join(info['columns_list'][:5])}")
        if len(info['columns_list']) > 5:
            print(f"              ... и еще {len(info['columns_list']) - 5}")
        print("="*60 + "\n")

# ===================================== Тестирование модуля =====================================

if __name__ == "__main__":
    """Тестирование функций модуля"""
    print("🧪 Тестирование модуля csv_manager.py\n")
    
    # Тест 1: Загрузка данных
    print("Тест 1: Загрузка исходных данных")
    csv_data, csv_file = load_initial_csv()
    if csv_data and csv_file:
        print("✅ PASSED\n")
    else:
        print("❌ FAILED\n")
    
    # Тест 2: Получение информации
    print("Тест 2: Получение информации о данных")
    info = get_csv_info()
    if info:
        print("✅ PASSED")
        _print_csv_stats()
    else:
        print("❌ FAILED\n")
    
    # Тест 3: Валидация
    print("Тест 3: Валидация данных")
    is_valid, message = validate_csv_data()
    print(f"Результат: {message}")
    if is_valid:
        print("✅ PASSED\n")
    else:
        print("❌ FAILED\n")
    
    # Тест 4: Создание бэкапа
    print("Тест 4: Создание бэкапа")
    backup_path = backup_current_data("test_backup.csv")
    if backup_path:
        print("✅ PASSED\n")
    else:
        print("❌ FAILED\n")
    
    # Тест 5: Работа с DataFrame
    print("Тест 5: Получение DataFrame")
    df = get_dataframe()
    if df is not None:
        print(f"✅ PASSED - DataFrame shape: {df.shape}\n")
    else:
        print("❌ FAILED\n")
    
    # Тест 6: Обновление данных
    print("Тест 6: Обновление данных")
    test_data = "col1,col2\n1,2\n3,4"
    if set_current_csv_data(test_data):
        print("✅ PASSED\n")
        # Восстанавливаем исходные данные
        reset_to_initial()
    else:
        print("❌ FAILED\n")
    
    print("🎉 Тестирование завершено!")