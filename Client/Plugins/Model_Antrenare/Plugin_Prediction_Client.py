"""
PLUGIN 8: Prediction Client - Live Predictions
Уровень: 8, Режим: Последовательно
Task: Load trained models and make live predictions
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Client/Client_Template')))
import Client_Template as base

base.CLIENT_NAME = "Prediction_Client"
base.CLIENT_LEVEL = "8"
base.CLIENT_MODE = "Sequential"


def do_work():
    import pandas as pd
    import io
    import pickle
    import os.path
    import json

    csv_data = base.csv_data

    if not csv_data:
        return "Error: CSV data not received", None

    try:
        # Проверяем наличие обученных моделей
        model1_path = 'model1_trained.pkl'
        model2_path = 'model2_trained.pkl'

        if not os.path.exists(model1_path):
            return "❌ Model1 not found! Please train Model1 first.", None

        if not os.path.exists(model2_path):
            return "❌ Model2 not found! Please train Model2 first.", None

        # Загружаем обе модели
        with open(model1_path, 'rb') as f:
            model1_data = pickle.load(f)

        with open(model2_path, 'rb') as f:
            model2_data = pickle.load(f)

        model1 = model1_data['model']
        model1_features = model1_data['feature_cols']
        model1_le_dict = model1_data['le_dict']
        model1_le_target = model1_data['le_target']

        model2 = model2_data['model']
        model2_features = model2_data['feature_cols']
        model2_le_dict = model2_data['le_dict']
        model2_le_target = model2_data['le_target']

        # Читаем новые данные для предсказания
        df = pd.read_csv(io.StringIO(csv_data))

        # Берем первые 10 строк для тестирования (или все данные)
        test_samples = df.head(10).copy()

        print("\n" + "=" * 70)
        print("🔮 PREDICTION CLIENT - Making Live Predictions")
        print("=" * 70)

        predictions = []

        for idx, row in test_samples.iterrows():
            print(f"\n📊 Sample {idx + 1}:")
            print(f"   Size: {row['size (cm)']} cm")
            print(f"   Shape: {row['shape']}")
            print(f"   Weight: {row['weight (g)']} g")
            print(f"   Price: {row['avg_price (MDL)']} MDL")
            print(f"   Color: {row['color']}")
            print(f"   Taste: {row['taste']}")

            # === PREDICTION MODEL 1 (Binary: fruit vs vegetable) ===
            # Подготовка данных для Model1
            X1_sample = []
            X1_sample.append(row['size (cm)'])
            X1_sample.append(row['weight (g)'])
            X1_sample.append(row['avg_price (MDL)'])

            # Кодируем категориальные признаки для Model1
            for col in ['shape', 'color', 'taste']:
                le = model1_le_dict[col]
                val = str(row[col])
                if val in le.classes_:
                    encoded_val = le.transform([val])[0]
                else:
                    # Если значение неизвестно, используем самое частое
                    encoded_val = 0
                X1_sample.append(encoded_val)

            # Предсказание Model1
            import numpy as np
            X1_sample = np.array(X1_sample).reshape(1, -1)
            pred1_encoded = model1.predict(X1_sample)[0]
            pred1_label = model1_le_target.inverse_transform([pred1_encoded])[0]
            pred1_proba = model1.predict_proba(X1_sample)[0]

            print(f"\n   🎯 Model 1 Prediction (Binary):")
            print(f"      Type: {pred1_label.upper()}")
            print(f"      Confidence: {max(pred1_proba) * 100:.2f}%")

            # === PREDICTION MODEL 2 (Multi-class: predict name) ===
            # Подготовка данных для Model2
            X2_sample = []
            X2_sample.append(row['size (cm)'])
            X2_sample.append(row['weight (g)'])
            X2_sample.append(row['avg_price (MDL)'])

            # Кодируем категориальные признаки для Model2
            for col in ['shape', 'color', 'taste', 'type']:
                le = model2_le_dict[col]
                # Для 'type' используем предсказание Model1
                if col == 'type':
                    val = pred1_label
                else:
                    val = str(row[col])

                if val in le.classes_:
                    encoded_val = le.transform([val])[0]
                else:
                    encoded_val = 0
                X2_sample.append(encoded_val)

            # Предсказание Model2
            X2_sample = np.array(X2_sample).reshape(1, -1)
            pred2_encoded = model2.predict(X2_sample)[0]
            pred2_label = model2_le_target.inverse_transform([pred2_encoded])[0]
            pred2_proba = model2.predict_proba(X2_sample)[0]

            # Топ-3 предсказания
            top3_indices = np.argsort(pred2_proba)[-3:][::-1]
            top3_labels = model2_le_target.inverse_transform(top3_indices)
            top3_probas = pred2_proba[top3_indices]

            print(f"\n   🎯 Model 2 Prediction (Multi-class):")
            print(f"      Name: {pred2_label.upper()}")
            print(f"      Confidence: {max(pred2_proba) * 100:.2f}%")
            print(f"\n      Top 3 predictions:")
            for i, (label, proba) in enumerate(zip(top3_labels, top3_probas), 1):
                print(f"         {i}. {label} ({proba * 100:.2f}%)")

            # Проверяем с реальным значением если есть
            if 'type' in row and 'name' in row:
                actual_type = row['type']
                actual_name = row['name']

                model1_correct = "✅" if pred1_label == actual_type else "❌"
                model2_correct = "✅" if pred2_label == actual_name else "❌"

                print(f"\n   📝 Actual values:")
                print(f"      Type: {actual_type} {model1_correct}")
                print(f"      Name: {actual_name} {model2_correct}")

            # Сохраняем результат
            prediction = {
                'sample_id': int(idx),
                'input': {
                    'size': float(row['size (cm)']),
                    'shape': str(row['shape']),
                    'weight': float(row['weight (g)']),
                    'price': float(row['avg_price (MDL)']),
                    'color': str(row['color']),
                    'taste': str(row['taste'])
                },
                'predictions': {
                    'model1': {
                        'type': pred1_label,
                        'confidence': float(max(pred1_proba))
                    },
                    'model2': {
                        'name': pred2_label,
                        'confidence': float(max(pred2_proba)),
                        'top3': [
                            {'name': label, 'confidence': float(proba)}
                            for label, proba in zip(top3_labels, top3_probas)
                        ]
                    }
                }
            }

            if 'type' in row and 'name' in row:
                prediction['actual'] = {
                    'type': str(row['type']),
                    'name': str(row['name'])
                }
                prediction['correct'] = {
                    'model1': pred1_label == row['type'],
                    'model2': pred2_label == row['name']
                }

            predictions.append(prediction)

            print("-" * 70)

        # Сохраняем все предсказания в JSON
        with open('predictions_results.json', 'w') as f:
            json.dump(predictions, f, indent=2)

        # Подсчитываем точность если есть реальные значения
        if 'type' in test_samples.columns and 'name' in test_samples.columns:
            model1_accuracy = sum(1 for p in predictions if p.get('correct', {}).get('model1', False)) / len(
                predictions)
            model2_accuracy = sum(1 for p in predictions if p.get('correct', {}).get('model2', False)) / len(
                predictions)

            print(f"\n📈 Accuracy on {len(predictions)} samples:")
            print(f"   Model 1 (Binary): {model1_accuracy * 100:.2f}%")
            print(f"   Model 2 (Multi-class): {model2_accuracy * 100:.2f}%")

        print("\n💾 Results saved to: predictions_results.json")
        print("=" * 70 + "\n")

        result_msg = (
            f"Prediction_Client: Made {len(predictions)} predictions.\n"
            f"Results saved to predictions_results.json"
        )

        # Добавляем предсказания в CSV
        for i, pred in enumerate(predictions):
            idx = pred['sample_id']
            df.loc[idx, 'predicted_type'] = pred['predictions']['model1']['type']
            df.loc[idx, 'predicted_name'] = pred['predictions']['model2']['name']
            df.loc[idx, 'prediction_confidence_type'] = pred['predictions']['model1']['confidence']
            df.loc[idx, 'prediction_confidence_name'] = pred['predictions']['model2']['confidence']

        result_csv = df.to_csv(index=False)

        return result_msg, result_csv

    except Exception as e:
        import traceback
        error_msg = f"Prediction_Client: Error - {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return error_msg, None


base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()