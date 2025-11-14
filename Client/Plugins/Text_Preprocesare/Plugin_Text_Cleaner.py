"""
PLUGIN 1: Text Cleaner
Уровень: 1, Режим: Последовательно
"""
import sys
import os
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../client/client_template')))
import Client_Template as base

base.CLIENT_NAME = "Text_Cleaner"
base.CLIENT_LEVEL = "1"
base.CLIENT_MODE = "Последовательно"

def do_work():
    """
    Плагин 1: Очистка текста
    """
    # === ПРИЕМ ДАННЫХ ===
    # TODO: Здесь будут приходить данные от сервера
    input_data = None  # Данные от сервера
    
    # Для тестирования используем заглушку
    raw_texts = [
        "Great product!!! Excellent quality... Fast delivery!!!",
        "BAD service?? Terrible experience! Poor quality...",
        "Amazing phone!!! Love the battery life. Wonderful screen!!!",
        "Not worth the money. Disappointed with purchase.",
        "Perfect! Exactly what I needed. Highly recommend!!!"
    ]
    
    # === ОБРАБОТКА ===
    cleaned_results = []
    
    for text in raw_texts:
        # Приводим к нижнему регистру
        cleaned = text.lower()
        
        # Удаляем специальные символы (оставляем только буквы и пробелы)
        cleaned = re.sub(r'[^a-zA-Z\s]', '', cleaned)
        
        # Удаляем лишние пробелы
        cleaned = ' '.join(cleaned.split())
        
        cleaned_results.append(cleaned)
    
    # === ВЫДАЧА ДАННЫХ ===
    output_data = cleaned_results
    
    print(f"[{base.CLIENT_NAME}] Cleaned {len(cleaned_results)} texts")
    
    # return json.dumps(output_data, ensure_ascii=False, indent=2)
    return f"Text_Cleaner: Обработано {len(cleaned_results)} текстов"

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()