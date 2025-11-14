"""
PLUGIN 5: Model 1 - Validation
Уровень: 5, Режим: Параллельно
"""
import sys
import os
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../client/client_template')))
import Client_Template as base

base.CLIENT_NAME = "Model1_Validation"
base.CLIENT_LEVEL = "5"
base.CLIENT_MODE = "Параллельно"

def do_work():
    """
    Плагин 5: Валидация первой модели
    """
    # === ПРИЕМ ДАННЫХ ===
    # TODO: Здесь будут приходить данные от Model1_Training (обученная модель)
    input_data = None  # Обученная модель от Model1_Training
    
    # Для тестирования используем заглушку
    validation_data = [
        {"text": "excellent service fast shipping", "true_label": "positive"},
        {"text": "poor quality bad experience", "true_label": "negative"},
        {"text": "amazing product highly recommend", "true_label": "positive"}
    ]
    
    # === ОБРАБОТКА (ВАЛИДАЦИЯ) ===
    correct = 0
    predictions = []
    
    for sample in validation_data:
        # Симулируем предсказание модели
        predicted = sample["true_label"] if random.random() > 0.15 else ("negative" if sample["true_label"] == "positive" else "positive")
        is_correct = predicted == sample["true_label"]
        if is_correct:
            correct += 1
        predictions.append(is_correct)
    
    accuracy = round(correct / len(validation_data), 4)
    precision = round(random.uniform(0.82, 0.94), 4)
    recall = round(random.uniform(0.80, 0.92), 4)
    f1_score = round(random.uniform(0.81, 0.93), 4)
    
    validation_results = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "total_samples": len(validation_data),
        "correct": correct
    }
    
    # === ВЫДАЧА ДАННЫХ ===
    output_data = validation_results
    
    print(f"[{base.CLIENT_NAME}] Validated {len(validation_data)} samples")
    print(f"[{base.CLIENT_NAME}] Accuracy: {accuracy}")
    print(f"[{base.CLIENT_NAME}] F1-Score: {f1_score}")
    
    # return json.dumps(output_data, ensure_ascii=False, indent=2)
    return f"Model1_Validation: Точность={accuracy}, F1={f1_score}"

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()