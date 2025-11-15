"""
PLUGIN 7: Model 2 - Validation
Уровень: 7, Режим: Параллельно
Task: Validate multi-class classification model
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Client/Client_Template')))
import Client_Template as base

base.CLIENT_NAME = "Model2_Validation"
base.CLIENT_LEVEL = "7"
base.CLIENT_MODE = "Параллельно"

def do_work():
    import pandas as pd
    import io
    import pickle
    import os.path
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from sklearn.model_selection import cross_val_score
    import json
    import numpy as np

    csv_data = base.csv_data

    if not csv_data:
        return "Ошибка: CSV данные не получены", None

    try:
        # Загружаем обученную модель
        model_path = 'model2_trained.pkl'
        if not os.path.exists(model_path):
            return "Ошибка: Модель Model2 не найдена. Сначала запустите Model2_Training", None

        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        model = model_data['model']
        feature_cols = model_data['feature_cols']
        le_dict = model_data['le_dict']
        le_target = model_data['le_target']

        df = pd.read_csv(io.StringIO(csv_data))

        # Фильтруем только данные для Model2
        df_model2 = df[df['model_target'] == 'model2'].copy()

        if len(df_model2) == 0:
            return "Ошибка: Нет данных для Model2", None

        # === ПОДГОТОВКА ДАННЫХ ДЛЯ ВАЛИДАЦИИ ===
        # Применяем те же преобразования
        categorical_cols = ['shape', 'color', 'taste', 'type']
        for col in categorical_cols:
            le = le_dict[col]
            df_model2[f'{col}_encoded'] = df_model2[col].astype(str).map(
                lambda x: le.transform([x])[0] if x in le.classes_ else -1
            )

        y_true = le_target.transform(df_model2['name'])
        X = df_model2[feature_cols]

        # === ВАЛИДАЦИЯ ===
        y_pred = model.predict(X)
        accuracy = accuracy_score(y_true, y_pred)

        # Cross-validation (на всех данных)
        cv_scores = cross_val_score(model, X, y_true, cv=min(5, len(set(y_true))))
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()

        # Classification report (только для топ классов, чтобы не перегружать вывод)
        class_report = classification_report(
            y_true, y_pred,
            target_names=le_target.classes_,
            output_dict=True,
            zero_division=0
        )

        # Confusion matrix
        conf_matrix = confusion_matrix(y_true, y_pred)

        # Top-3 и Bottom-3 классов по F1-score
        f1_scores = {cls: class_report[cls]['f1-score']
                     for cls in le_target.classes_ if cls in class_report}
        sorted_f1 = sorted(f1_scores.items(), key=lambda x: x[1], reverse=True)
        top_3 = sorted_f1[:3]
        bottom_3 = sorted_f1[-3:] if len(sorted_f1) > 3 else []

        # === РЕЗУЛЬТАТЫ ===
        validation_results = {
            'accuracy': accuracy,
            'cv_mean': cv_mean,
            'cv_std': cv_std,
            'n_classes': len(le_target.classes_),
            'classification_report': class_report,
            'confusion_matrix': conf_matrix.tolist(),
            'classes': le_target.classes_.tolist(),
            'top_3_classes': top_3,
            'bottom_3_classes': bottom_3
        }

        # Добавляем результаты валидации в CSV
        df_model2['model2_validated'] = 'yes'
        df_model2['model2_val_accuracy'] = accuracy
        df_model2['model2_cv_mean'] = cv_mean

        # Объединяем с остальными данными
        df_other = df[df['model_target'] != 'model2']
        df_final = pd.concat([df_model2, df_other], ignore_index=True)

        result_csv = df_final.to_csv(index=False)

        result_msg = (
            f"Model2_Validation: Random Forest validated\n"
            f"Validation Accuracy: {accuracy:.4f}\n"
            f"Cross-Validation: {cv_mean:.4f} (+/- {cv_std:.4f})\n"
            f"Number of classes: {len(le_target.classes_)}\n\n"
            f"Top 3 classes (by F1-score):\n"
        )

        for cls, score in top_3:
            if cls in class_report:
                result_msg += f"  {cls}: F1={score:.3f}, precision={class_report[cls]['precision']:.3f}, recall={class_report[cls]['recall']:.3f}\n"

        if bottom_3:
            result_msg += f"\nBottom 3 classes (by F1-score):\n"
            for cls, score in bottom_3:
                if cls in class_report:
                    result_msg += f"  {cls}: F1={score:.3f}, precision={class_report[cls]['precision']:.3f}, recall={class_report[cls]['recall']:.3f}\n"

        print(f"\n{'='*60}")
        print(result_msg)
        print(f"Confusion Matrix shape: {conf_matrix.shape}")
        print(f"{'='*60}\n")

        # Сохраняем детальный отчет
        with open('model2_validation_report.json', 'w') as f:
            # Конвертируем numpy arrays в списки для JSON
            validation_results_json = validation_results.copy()
            validation_results_json['confusion_matrix'] = conf_matrix.tolist()
            json.dump(validation_results_json, f, indent=2)

        return result_msg, result_csv

    except Exception as e:
        import traceback
        error_msg = f"Model2_Validation: Ошибка - {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return error_msg, None

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()
