"""
PLUGIN 7: Model 2 - Validation
Уровень: 5, Режим: Параллельно
"""
import sys
import os
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../client/client_template')))
import Client_Template as base

base.CLIENT_NAME = "Model2_Validation"
base.CLIENT_LEVEL = "5"
base.CLIENT_MODE = "Параллельно"

def do_work():
    """
    Плагин 7: Валидация второй модели
    """
    # === ПРИЕМ ДАННЫХ ===
    # TODO: Здесь будут приходить данные от Model2_Training (обученная модель)
    input_data = None  # Обученная модель от Model2_Training
    
    # Для тестирования используем заглушку
    validation_data = [
        {"text": "disappointed terrible waste money", "true_label": "negative"},
        {"text": "perfect exactly needed highly", "true_label": "positive"}
    ]
    
    # === ОБРАБОТКА (ВАЛИДАЦИЯ) ===
    correct = 0
    predictions = []
    
    for sample in validation_data:
        # Симулируем предсказание модели
        predicted = sample["true_label"] if random.random() > 0.20 else ("negative" if sample["true_label"] == "positive" else "positive")
        is_correct = predicted == sample["true_label"]
        if is_correct:
            correct += 1
        predictions.append(is_correct)
    
    accuracy = round(correct / len(validation_data), 4)
    precision = round(random.uniform(0.78, 0.90), 4)
    recall = round(random.uniform(0.76, 0.88), 4)
    f1_score = round(random.uniform(0.77, 0.89), 4)
    
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
    return f"Model2_Validation: Точность={accuracy}, F1={f1_score}"

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()