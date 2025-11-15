"""
PLUGIN 5: Model 1 - Validation
Уровень: 5, Режим: Параллельно
Task: Validate binary classification model
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Client/Client_Template')))
import Client_Template as base

base.CLIENT_NAME = "Model1_Validation"
base.CLIENT_LEVEL = "5"
base.CLIENT_MODE = "Параллельно"

def do_work():
    import pandas as pd
    import io
    import pickle
    import os.path
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from sklearn.model_selection import cross_val_score
    import json

    csv_data = base.csv_data

    if not csv_data:
        return "Ошибка: CSV данные не получены", None

    try:
        # Загружаем обученную модель
        model_path = 'model1_trained.pkl'
        if not os.path.exists(model_path):
            return "Ошибка: Модель Model1 не найдена. Сначала запустите Model1_Training", None

        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        model = model_data['model']
        feature_cols = model_data['feature_cols']
        le_dict = model_data['le_dict']
        le_target = model_data['le_target']

        df = pd.read_csv(io.StringIO(csv_data))

        # Фильтруем только данные для Model1
        df_model1 = df[df['model_target'] == 'model1'].copy()

        if len(df_model1) == 0:
            return "Ошибка: Нет данных для Model1", None

        # === ПОДГОТОВКА ДАННЫХ ДЛЯ ВАЛИДАЦИИ ===
        # Применяем те же преобразования
        categorical_cols = ['shape', 'color', 'taste']
        for col in categorical_cols:
            le = le_dict[col]
            df_model1[f'{col}_encoded'] = df_model1[col].astype(str).map(
                lambda x: le.transform([x])[0] if x in le.classes_ else -1
            )

        y_true = le_target.transform(df_model1['type'])
        X = df_model1[feature_cols]

        # === ВАЛИДАЦИЯ ===
        y_pred = model.predict(X)
        accuracy = accuracy_score(y_true, y_pred)

        # Cross-validation (на всех данных)
        cv_scores = cross_val_score(model, X, y_true, cv=5)
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()

        # Classification report
        class_report = classification_report(
            y_true, y_pred,
            target_names=le_target.classes_,
            output_dict=True
        )

        # Confusion matrix
        conf_matrix = confusion_matrix(y_true, y_pred)

        # === РЕЗУЛЬТАТЫ ===
        validation_results = {
            'accuracy': accuracy,
            'cv_mean': cv_mean,
            'cv_std': cv_std,
            'classification_report': class_report,
            'confusion_matrix': conf_matrix.tolist(),
            'classes': le_target.classes_.tolist()
        }

        # Добавляем результаты валидации в CSV
        df_model1['model1_validated'] = 'yes'
        df_model1['model1_val_accuracy'] = accuracy
        df_model1['model1_cv_mean'] = cv_mean

        # Объединяем с остальными данными
        df_other = df[df['model_target'] != 'model1']
        df_final = pd.concat([df_model1, df_other], ignore_index=True)

        result_csv = df_final.to_csv(index=False)

        result_msg = (
            f"Model1_Validation: Decision Tree validated\n"
            f"Validation Accuracy: {accuracy:.4f}\n"
            f"Cross-Validation: {cv_mean:.4f} (+/- {cv_std:.4f})\n"
            f"Classes: {le_target.classes_.tolist()}\n\n"
            f"Classification Report:\n"
        )

        for cls in le_target.classes_:
            if cls in class_report:
                result_msg += f"  {cls}: precision={class_report[cls]['precision']:.3f}, recall={class_report[cls]['recall']:.3f}, f1={class_report[cls]['f1-score']:.3f}\n"

        print(f"\n{'='*60}")
        print(result_msg)
        print(f"Confusion Matrix:\n{conf_matrix}")
        print(f"{'='*60}\n")

        # Сохраняем детальный отчет
        with open('model1_validation_report.json', 'w') as f:
            json.dump(validation_results, f, indent=2)

        return result_msg, result_csv

    except Exception as e:
        import traceback
        error_msg = f"Model1_Validation: Ошибка - {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return error_msg, None

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()
