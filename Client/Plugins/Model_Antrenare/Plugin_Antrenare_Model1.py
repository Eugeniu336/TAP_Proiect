"""
PLUGIN 4: Model 1 - Training
Уровень: 4, Режим: Параллельно
"""
import sys
import os
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../client/client_template')))
import Client_Template as base

base.CLIENT_NAME = "Model1_Training"
base.CLIENT_LEVEL = "4"
base.CLIENT_MODE = "Параллельно"

def do_work():
    """
    Плагин 4: Обучение первой модели
    """
    # === ПРИЕМ ДАННЫХ ===
    # TODO: Здесь будут приходить данные от Lemmatizer (первая половина)
    input_data = None  # Данные от Lemmatizer
    
    # Для тестирования используем заглушку
    model1_data = [
        ["great", "product", "excellent", "quality", "fast", "delivery"],
        ["bad", "service", "terrible", "experience", "poor", "quality"],
        ["amazing", "phone", "love", "the", "battery", "life", "wonderful", "screen"]
    ]
    
    # === ОБРАБОТКА (ОБУЧЕНИЕ) ===
    vocab_size = len(set([word for tokens in model1_data for word in tokens]))
    total_words = sum(len(tokens) for tokens in model1_data)
    
    # Симулируем процесс обучения
    epochs = 10
    initial_loss = round(random.uniform(2.5, 3.5), 4)
    final_loss = round(random.uniform(0.3, 0.8), 4)
    training_accuracy = round(random.uniform(0.85, 0.95), 4)
    
    trained_model = {
        "vocab_size": vocab_size,
        "training_samples": len(model1_data),
        "epochs": epochs,
        "final_loss": final_loss,
        "accuracy": training_accuracy
    }
    
    # === ВЫДАЧА ДАННЫХ ===
    # Обученная модель будет передана в Model1_Validation
    output_data = trained_model
    
    print(f"[{base.CLIENT_NAME}] Trained on {len(model1_data)} samples")
    print(f"[{base.CLIENT_NAME}] Vocab size: {vocab_size}")
    print(f"[{base.CLIENT_NAME}] Final Loss: {final_loss}")
    print(f"[{base.CLIENT_NAME}] Accuracy: {training_accuracy}")
    
    # return json.dumps(output_data, ensure_ascii=False, indent=2)
    return f"Model1_Training: Обучено на {len(model1_data)} образцах. Accuracy={training_accuracy}"

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()