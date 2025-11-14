"""
PLUGIN 3: Lemmatizer & Splitter
Уровень: 3, Режим: Последовательно
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../client/client_template')))
import Client_Template as base

base.CLIENT_NAME = "Lemmatizer"
base.CLIENT_LEVEL = "3"
base.CLIENT_MODE = "Последовательно"

# Простой словарь лемматизации
LEMMA_DICT = {
    "products": "product", "services": "service", "phones": "phone",
    "loves": "love", "batteries": "battery", "lives": "life",
    "screens": "screen", "disappointed": "disappoint", 
    "purchases": "purchase", "needed": "need"
}

def do_work():
    """
    Плагин 3: Лемматизация и разделение данных на 2 половины
    """
    # === ПРИЕМ ДАННЫХ ===
    # TODO: Здесь будут приходить данные от Tokenizer
    input_data = None  # Данные от предыдущего плагина
    
    # Для тестирования используем заглушку (токенизированные тексты)
    tokenized_data = [
        ["great", "product", "excellent", "quality", "fast", "delivery"],
        ["bad", "service", "terrible", "experience", "poor", "quality"],
        ["amazing", "phone", "love", "the", "battery", "life", "wonderful", "screen"],
        ["not", "worth", "the", "money", "disappointed", "with", "purchase"],
        ["perfect", "exactly", "what", "needed", "highly", "recommend"]
    ]
    
    # === ОБРАБОТКА ===
    lemmatized_results = []
    
    for tokens in tokenized_data:
        # Лемматизация токенов
        lemmas = [LEMMA_DICT.get(token, token) for token in tokens]
        lemmatized_results.append(lemmas)
    
    # === РАЗДЕЛЕНИЕ НА ДВЕ ПОЛОВИНЫ ===
    mid_point = len(lemmatized_results) // 2
    
    model1_data = lemmatized_results[:mid_point + len(lemmatized_results) % 2]
    model2_data = lemmatized_results[mid_point + len(lemmatized_results) % 2:]
    
    # === ВЫДАЧА ДАННЫХ ===
    # Данные будут отправлены на Model1_Training и Model2_Training
    output_data = {
        "model1": model1_data,
        "model2": model2_data
    }
    
    print(f"[{base.CLIENT_NAME}] Lemmatized {len(lemmatized_results)} texts")
    print(f"[{base.CLIENT_NAME}] Model 1: {len(model1_data)} samples")
    print(f"[{base.CLIENT_NAME}] Model 2: {len(model2_data)} samples")
    
    # return json.dumps(output_data, ensure_ascii=False, indent=2)
    return f"Lemmatizer: Обработано {len(lemmatized_results)} текстов. Model1={len(model1_data)}, Model2={len(model2_data)}"

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()