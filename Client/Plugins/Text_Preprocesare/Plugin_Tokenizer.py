"""
PLUGIN 2: Tokenizer
Уровень: 2, Режим: Последовательно
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../client/client_template')))
import Client_Template as base

base.CLIENT_NAME = "Tokenizer"
base.CLIENT_LEVEL = "2"
base.CLIENT_MODE = "Последовательно"

def do_work():
    """
    Плагин 2: Токенизация
    """
    # === ПРИЕМ ДАННЫХ ===
    # TODO: Здесь будут приходить данные от Text_Cleaner
    input_data = None  # Данные от предыдущего плагина
    
    # Для тестирования используем заглушку (очищенные тексты)
    cleaned_texts = [
        "great product excellent quality fast delivery",
        "bad service terrible experience poor quality",
        "amazing phone love the battery life wonderful screen",
        "not worth the money disappointed with purchase",
        "perfect exactly what i needed highly recommend"
    ]
    
    # === ОБРАБОТКА ===
    tokenized_results = []
    
    for text in cleaned_texts:
        # Токенизация по пробелам
        tokens = text.split()
        
        # Фильтруем слишком короткие токены (меньше 2 символов)
        tokens = [t for t in tokens if len(t) > 1]
        
        tokenized_results.append(tokens)
    
    # === ВЫДАЧА ДАННЫХ ===
    output_data = tokenized_results
    
    total_tokens = sum(len(tokens) for tokens in tokenized_results)
    print(f"[{base.CLIENT_NAME}] Tokenized {len(tokenized_results)} texts")
    print(f"[{base.CLIENT_NAME}] Total tokens: {total_tokens}")
    
    # return json.dumps(output_data, ensure_ascii=False, indent=2)
    return f"Tokenizer: Токенизировано {len(tokenized_results)} текстов, всего {total_tokens} токенов"

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()