"""
PLUGIN 4: Model 1 - Training (Decision Tree)
Уровень: 4, Режим: Параллельно
Task: Binary classification (fruit vs vegetable)
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Client/Client_Template')))
import Client_Template as base

base.CLIENT_NAME = "Model1_Training"
base.CLIENT_LEVEL = "4"
base.CLIENT_MODE = "Parallel"

def do_work():
    import pandas as pd
    import io
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    import pickle
    import json

    csv_data = base.csv_data

    if not csv_data:
        return "Error: CSV data not received", None

    try:
        df = pd.read_csv(io.StringIO(csv_data))

        # Фильтруем только данные для Model1
        df_model1 = df[df['model_target'] == 'model1'].copy()

        if len(df_model1) == 0:
            return "Error: No data for Model1", None

        # === ПОДГОТОВКА ДАННЫХ ===
        # Features: size, weight, avg_price + encoded: shape, color, taste
        feature_cols = ['size (cm)', 'weight (g)', 'avg_price (MDL)']
        categorical_cols = ['shape', 'color', 'taste']

        # Проверяем наличие колонок
        missing_cols = [col for col in feature_cols + categorical_cols if col not in df_model1.columns]
        if missing_cols:
            return f"Error: Missing columns {missing_cols}", None

        # Кодируем категориальные признаки
        le_dict = {}
        for col in categorical_cols:
            le = LabelEncoder()
            df_model1[f'{col}_encoded'] = le.fit_transform(df_model1[col].astype(str))
            le_dict[col] = le
            feature_cols.append(f'{col}_encoded')

        # Target: type (fruit/vegetable)
        if 'type' not in df_model1.columns:
            return "Error: Column 'type' not found", None

        le_target = LabelEncoder()
        y = le_target.fit_transform(df_model1['type'])
        X = df_model1[feature_cols]

        # Разделение на train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # === ОБУЧЕНИЕ МОДЕЛИ ===
        model = DecisionTreeClassifier(
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )

        model.fit(X_train, y_train)

        # === МЕТРИКИ ===
        train_acc = model.score(X_train, y_train)
        test_acc = model.score(X_test, y_test)

        # Сохраняем модель в память для передачи в Validation
        model_data = {
            'model': model,
            'feature_cols': feature_cols,
            'le_dict': le_dict,
            'le_target': le_target,
            'train_acc': train_acc,
            'test_acc': test_acc,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'classes': le_target.classes_.tolist()
        }

        # Добавляем модель в CSV для передачи дальше
        df_model1['model1_trained'] = 'yes'
        df_model1['model1_train_acc'] = train_acc
        df_model1['model1_test_acc'] = test_acc

        # Сохраняем модель в файл для Plugin 5
        model_path = 'model1_trained.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)

        # Объединяем с остальными данными
        df_other = df[df['model_target'] != 'model1']
        df_final = pd.concat([df_model1, df_other], ignore_index=True)

        result_csv = df_final.to_csv(index=False)
        result_msg = (
            f"Model1_Training: Decision Tree trained on {len(X_train)} samples.\n"
            f"Train Accuracy: {train_acc:.4f}, Test Accuracy: {test_acc:.4f}\n"
            f"Classes: {le_target.classes_.tolist()}"
        )

        print(f"\n{'='*60}")
        print(result_msg)
        print(f"{'='*60}\n")

        return result_msg, result_csv

    except Exception as e:
        import traceback
        error_msg = f"Model1_Training: Error - {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return error_msg, None

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()