"""
PLUGIN 6: Model 2 - Training (Random Forest)
Уровень: 6, Режим: Параллельно
Task: Multi-class classification (predict fruit/vegetable name)
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Client/Client_Template')))
import Client_Template as base

base.CLIENT_NAME = "Model2_Training"
base.CLIENT_LEVEL = "6"
base.CLIENT_MODE = "Parallel"

def do_work():
    import pandas as pd
    import io
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    import pickle
    import json

    csv_data = base.csv_data

    if not csv_data:
        return "Error: CSV data not received", None

    try:
        df = pd.read_csv(io.StringIO(csv_data))

        # Фильтруем только данные для Model2
        df_model2 = df[df['model_target'] == 'model2'].copy()

        if len(df_model2) == 0:
            return "Error: No data for Model2", None

        # === ПОДГОТОВКА ДАННЫХ ===
        # Features: size, weight, avg_price + encoded: shape, color, taste, type
        feature_cols = ['size (cm)', 'weight (g)', 'avg_price (MDL)']
        categorical_cols = ['shape', 'color', 'taste', 'type']

        # Проверяем наличие колонок
        missing_cols = [col for col in feature_cols + categorical_cols if col not in df_model2.columns]
        if missing_cols:
            return f"Error: Missing columns {missing_cols}", None

        # Кодируем категориальные признаки
        le_dict = {}
        for col in categorical_cols:
            le = LabelEncoder()
            df_model2[f'{col}_encoded'] = le.fit_transform(df_model2[col].astype(str))
            le_dict[col] = le
            feature_cols.append(f'{col}_encoded')

        # Target: name (название фрукта/овоща)
        if 'name' not in df_model2.columns:
            return "Error: Column 'name' not found", None

        le_target = LabelEncoder()
        y = le_target.fit_transform(df_model2['name'])
        X = df_model2[feature_cols]

        # Разделение на train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
        )

        # === ОБУЧЕНИЕ МОДЕЛИ ===
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

        # === МЕТРИКИ ===
        train_acc = model.score(X_train, y_train)
        test_acc = model.score(X_test, y_test)

        # Feature importance
        feature_importance = dict(zip(feature_cols, model.feature_importances_))
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]

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
            'n_classes': len(le_target.classes_),
            'classes': le_target.classes_.tolist(),
            'feature_importance': feature_importance
        }

        # Добавляем модель в CSV для передачи дальше
        df_model2['model2_trained'] = 'yes'
        df_model2['model2_train_acc'] = train_acc
        df_model2['model2_test_acc'] = test_acc

        # Сохраняем модель в файл для Plugin 7
        model_path = 'model2_trained.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)

        # Объединяем с остальными данными
        df_other = df[df['model_target'] != 'model2']
        df_final = pd.concat([df_model2, df_other], ignore_index=True)

        result_csv = df_final.to_csv(index=False)
        result_msg = (
            f"Model2_Training: Random Forest trained on {len(X_train)} samples.\n"
            f"Train Accuracy: {train_acc:.4f}, Test Accuracy: {test_acc:.4f}\n"
            f"Number of classes: {len(le_target.classes_)}\n"
            f"Top 5 features:\n"
        )

        for feat, imp in top_features:
            result_msg += f"  {feat}: {imp:.4f}\n"

        print(f"\n{'='*60}")
        print(result_msg)
        print(f"{'='*60}\n")

        return result_msg, result_csv

    except Exception as e:
        import traceback
        error_msg = f"Model2_Training: Error - {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return error_msg, None

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()