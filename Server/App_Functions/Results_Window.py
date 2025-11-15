import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import io
import pickle
import os
import json
import pandas as pd
import numpy as np

from App_Functions.CSV_Manager import get_current_csv_data

def show_results_window():
    """Интерактивное окно с результатами и возможностью делать предсказания"""
    current_csv_data = get_current_csv_data()
    
    if not current_csv_data:
        messagebox.showinfo("Инфо", "Нет данных для отображения")
        return
    
    try:
        df = pd.read_csv(io.StringIO(current_csv_data))
        
        # Загружаем обученные модели
        model1_data = None
        model2_data = None
        
        if os.path.exists('model1_trained.pkl'):
            with open('model1_trained.pkl', 'rb') as f:
                model1_data = pickle.load(f)
        
        if os.path.exists('model2_trained.pkl'):
            with open('model2_trained.pkl', 'rb') as f:
                model2_data = pickle.load(f)
        
        # Создаём главное окно
        results_window = tk.Toplevel()
        results_window.title("🤖 AI Models Dashboard")
        results_window.geometry("900x700")
        
        # Notebook для вкладок
        notebook = ttk.Notebook(results_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ==================== ВКЛАДКА 1: Статистика моделей ====================
        create_stats_tab(notebook, df, model1_data, model2_data)
        
        # ==================== ВКЛАДКА 2: Интерактивные предсказания ====================
        create_predictions_tab(notebook, df, model1_data, model2_data)
        
        # ==================== ВКЛАДКА 3: История предсказаний ====================
        create_history_tab(notebook)
        
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось отобразить результаты:\n{e}")
        import traceback
        traceback.print_exc()

def create_stats_tab(notebook, df, model1_data, model2_data):
    """Создание вкладки статистики"""
    stats_frame = tk.Frame(notebook)
    notebook.add(stats_frame, text="📊 Статистика")
    
    stats_scroll = tk.Scrollbar(stats_frame)
    stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    stats_text = tk.Text(stats_frame, wrap=tk.WORD, yscrollcommand=stats_scroll.set,
                        font=("Courier", 10), bg="#f5f5f5")
    stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    stats_scroll.config(command=stats_text.yview)
    
    # Формируем статистику
    output = generate_stats_output(df, model1_data, model2_data)
    
    stats_text.insert("1.0", output)
    stats_text.config(state=tk.DISABLED)

def generate_stats_output(df, model1_data, model2_data):
    """Генерация текста статистики"""
    output = ""
    output += "=" * 80 + "\n"
    output += " " * 25 + "🎉 РЕЗУЛЬТАТЫ ОБУЧЕНИЯ 🎉\n"
    output += "=" * 80 + "\n\n"
    
    output += f"📂 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    output += f"📊 Всего записей: {len(df):,}\n"
    output += f"📋 Колонок: {len(df.columns)}\n\n"
    
    # Статистика предобработки
    output += "─" * 80 + "\n"
    output += "📝 ПРЕДОБРАБОТКА ДАННЫХ\n"
    output += "─" * 80 + "\n"
    
    if 'cleaned_text' in df.columns:
        output += f"✅ Text Cleaning: {df['cleaned_text'].notna().sum():,} записей\n"
    if 'tokens' in df.columns:
        output += f"✅ Tokenization: {df['tokens'].notna().sum():,} записей\n"
    if 'lemmas' in df.columns:
        output += f"✅ Lemmatization: {df['lemmas'].notna().sum():,} записей\n"
    
    if 'model_target' in df.columns:
        m1 = len(df[df['model_target'] == 'model1'])
        m2 = len(df[df['model_target'] == 'model2'])
        output += f"\n📊 Разделение данных:\n"
        output += f"   • Model 1 (Binary): {m1:,} ({m1/len(df)*100:.1f}%)\n"
        output += f"   • Model 2 (Multi-class): {m2:,} ({m2/len(df)*100:.1f}%)\n"
    
    output += "\n" + "─" * 80 + "\n"
    output += "🤖 МОДЕЛЬ 1: BINARY CLASSIFICATION (Decision Tree)\n"
    output += "─" * 80 + "\n"
    
    if model1_data:
        output += f"📈 Обучение:\n"
        output += f"   • Train Accuracy: {model1_data['train_acc']:.4f} ({model1_data['train_acc']*100:.2f}%)\n"
        output += f"   • Test Accuracy:  {model1_data['test_acc']:.4f} ({model1_data['test_acc']*100:.2f}%)\n"
        output += f"   • Train Size: {model1_data['train_size']:,} samples\n"
        output += f"   • Test Size:  {model1_data['test_size']:,} samples\n"
        output += f"   • Classes: {', '.join(model1_data['classes'])}\n"
        
        if 'model1_val_accuracy' in df.columns:
            val_acc = df['model1_val_accuracy'].iloc[0]
            cv_mean = df.get('model1_cv_mean', pd.Series([0])).iloc[0]
            output += f"\n📊 Валидация:\n"
            output += f"   • Validation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)\n"
            output += f"   • Cross-Validation: {cv_mean:.4f} ({cv_mean*100:.2f}%)\n"
    else:
        output += "❌ Модель не обучена\n"
    
    output += "\n" + "─" * 80 + "\n"
    output += "🤖 МОДЕЛЬ 2: MULTI-CLASS CLASSIFICATION (Random Forest)\n"
    output += "─" * 80 + "\n"
    
    if model2_data:
        output += f"📈 Обучение:\n"
        output += f"   • Train Accuracy: {model2_data['train_acc']:.4f} ({model2_data['train_acc']*100:.2f}%)\n"
        output += f"   • Test Accuracy:  {model2_data['test_acc']:.4f} ({model2_data['test_acc']*100:.2f}%)\n"
        output += f"   • Train Size: {model2_data['train_size']:,} samples\n"
        output += f"   • Test Size:  {model2_data['test_size']:,} samples\n"
        output += f"   • Number of Classes: {model2_data['n_classes']}\n"
        
        if 'feature_importance' in model2_data:
            top_features = sorted(model2_data['feature_importance'].items(), 
                                key=lambda x: x[1], reverse=True)[:5]
            output += f"\n📊 Top 5 Features:\n"
            for feat, imp in top_features:
                output += f"   • {feat}: {imp:.4f}\n"
        
        if 'model2_val_accuracy' in df.columns:
            val_acc = df['model2_val_accuracy'].iloc[0]
            cv_mean = df.get('model2_cv_mean', pd.Series([0])).iloc[0]
            output += f"\n📊 Валидация:\n"
            output += f"   • Validation Accuracy: {val_acc:.4f} ({val_acc*100:.2f}%)\n"
            output += f"   • Cross-Validation: {cv_mean:.4f} ({cv_mean*100:.2f}%)\n"
    else:
        output += "❌ Модель не обучена\n"
    
    output += "\n" + "=" * 80 + "\n"
    output += " " * 20 + "✨ МОДЕЛИ ГОТОВЫ К ИСПОЛЬЗОВАНИЮ ✨\n"
    output += "=" * 80 + "\n"
    
    return output

def create_predictions_tab(notebook, df, model1_data, model2_data):
    """Создание вкладки предсказаний"""
    predict_frame = tk.Frame(notebook, bg="#f0f0f0")
    notebook.add(predict_frame, text="🔮 Предсказания")
    
    # Заголовок
    title_frame = tk.Frame(predict_frame, bg="#4CAF50", height=60)
    title_frame.pack(fill=tk.X)
    title_frame.pack_propagate(False)
    
    tk.Label(title_frame, text="🔮 Тестирование моделей", 
            font=("Arial", 16, "bold"), bg="#4CAF50", fg="white").pack(pady=15)
    
    # Форма ввода
    input_frame, fields = create_input_form(predict_frame, df)
    
    # Результат
    result_frame = tk.Frame(predict_frame, bg="#ffffff", relief=tk.RIDGE, bd=2)
    result_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
    
    result_text = tk.Text(result_frame, wrap=tk.WORD, font=("Courier", 11), 
                         bg="#ffffff", height=12)
    result_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    # Кнопка предсказания
    btn_frame = tk.Frame(predict_frame, bg="#f0f0f0")
    btn_frame.pack(pady=10)
    
    predict_btn = tk.Button(btn_frame, text="🔮 Сделать предсказание", 
                           command=lambda: make_prediction(fields, result_text, model1_data, model2_data),
                           font=("Arial", 12, "bold"), 
                           bg="#4CAF50", fg="white",
                           width=25, height=2,
                           cursor="hand2")
    predict_btn.pack()

def create_input_form(parent, df):
    """Создание формы ввода данных"""
    input_frame = tk.Frame(parent, bg="#f0f0f0")
    input_frame.pack(pady=20, padx=20, fill=tk.BOTH)
    
    # Получаем уникальные значения из датасета
    unique_shapes = df['shape'].unique().tolist() if 'shape' in df.columns else []
    unique_colors = df['color'].unique().tolist() if 'color' in df.columns else []
    unique_tastes = df['taste'].unique().tolist() if 'taste' in df.columns else []
    
    fields = []
    
    row = 0
    tk.Label(input_frame, text="Размер (см):", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
    size_entry = tk.Entry(input_frame, font=("Arial", 11), width=20)
    size_entry.insert(0, "5.0")
    size_entry.grid(row=row, column=1, pady=8, padx=10)
    fields.append(("size", size_entry))
    
    row += 1
    tk.Label(input_frame, text="Вес (г):", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
    weight_entry = tk.Entry(input_frame, font=("Arial", 11), width=20)
    weight_entry.insert(0, "150")
    weight_entry.grid(row=row, column=1, pady=8, padx=10)
    fields.append(("weight", weight_entry))
    
    row += 1
    tk.Label(input_frame, text="Цена (₹):", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
    price_entry = tk.Entry(input_frame, font=("Arial", 11), width=20)
    price_entry.insert(0, "50")
    price_entry.grid(row=row, column=1, pady=8, padx=10)
    fields.append(("price", price_entry))
    
    row += 1
    tk.Label(input_frame, text="Форма:", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
    shape_var = tk.StringVar(value=unique_shapes[0] if unique_shapes else "round")
    shape_combo = ttk.Combobox(input_frame, textvariable=shape_var, values=unique_shapes, 
                               font=("Arial", 11), width=18, state="readonly")
    shape_combo.grid(row=row, column=1, pady=8, padx=10)
    fields.append(("shape", shape_var))
    
    row += 1
    tk.Label(input_frame, text="Цвет:", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
    color_var = tk.StringVar(value=unique_colors[0] if unique_colors else "red")
    color_combo = ttk.Combobox(input_frame, textvariable=color_var, values=unique_colors,
                               font=("Arial", 11), width=18, state="readonly")
    color_combo.grid(row=row, column=1, pady=8, padx=10)
    fields.append(("color", color_var))
    
    row += 1
    tk.Label(input_frame, text="Вкус:", font=("Arial", 11), bg="#f0f0f0").grid(row=row, column=0, sticky="w", pady=8)
    taste_var = tk.StringVar(value=unique_tastes[0] if unique_tastes else "sweet")
    taste_combo = ttk.Combobox(input_frame, textvariable=taste_var, values=unique_tastes,
                               font=("Arial", 11), width=18, state="readonly")
    taste_combo.grid(row=row, column=1, pady=8, padx=10)
    fields.append(("taste", taste_var))
    
    return input_frame, fields

def make_prediction(fields, result_text, model1_data, model2_data):
    """Функция предсказания"""
    if not model1_data or not model2_data:
        result_text.delete("1.0", tk.END)
        result_text.insert("1.0", "❌ Модели не обучены! Сначала запустите обучение.")
        return
    
    try:
        # Получаем данные из полей
        values = {}
        for name, widget in fields:
            if hasattr(widget, 'get'):
                val = widget.get()
                if name in ['size', 'weight', 'price']:
                    values[name] = float(val)
                else:
                    values[name] = val
        
        size = values['size']
        weight = values['weight']
        price = values['price']
        shape = values['shape']
        color = values['color']
        taste = values['taste']
        
        # === ПРЕДСКАЗАНИЕ MODEL 1 (Binary) ===
        X1_data = {
            'size (cm)': [size],
            'weight (g)': [weight],
            'avg_price (₹)': [price]
        }
        
        # Кодируем категориальные признаки для Model1
        for col in ['shape', 'color', 'taste']:
            le = model1_data['le_dict'][col]
            val = {'shape': shape, 'color': color, 'taste': taste}[col]
            if val in le.classes_:
                encoded = le.transform([val])[0]
            else:
                encoded = 0
            X1_data[f'{col}_encoded'] = [encoded]
        
        X1_sample = pd.DataFrame(X1_data)
        X1_sample = X1_sample[model1_data['feature_cols']]
        
        pred1_encoded = model1_data['model'].predict(X1_sample)[0]
        pred1_label = model1_data['le_target'].inverse_transform([pred1_encoded])[0]
        pred1_proba = model1_data['model'].predict_proba(X1_sample)[0]
        
        # === ПРЕДСКАЗАНИЕ MODEL 2 (Multi-class) ===
        X2_data = {
            'size (cm)': [size],
            'weight (g)': [weight],
            'avg_price (₹)': [price]
        }
        
        for col in ['shape', 'color', 'taste', 'type']:
            le = model2_data['le_dict'][col]
            if col == 'type':
                val = pred1_label
            else:
                val = {'shape': shape, 'color': color, 'taste': taste}[col]
            
            if val in le.classes_:
                encoded = le.transform([val])[0]
            else:
                encoded = 0
            X2_data[f'{col}_encoded'] = [encoded]
        
        X2_sample = pd.DataFrame(X2_data)
        X2_sample = X2_sample[model2_data['feature_cols']]
        
        pred2_encoded = model2_data['model'].predict(X2_sample)[0]
        pred2_label = model2_data['le_target'].inverse_transform([pred2_encoded])[0]
        pred2_proba = model2_data['model'].predict_proba(X2_sample)[0]
        
        # Топ-3 предсказания для Model2
        top3_indices = np.argsort(pred2_proba)[-3:][::-1]
        top3_labels = model2_data['le_target'].inverse_transform(top3_indices)
        top3_probas = pred2_proba[top3_indices]
        
        # Формируем результат
        result = generate_prediction_output(size, weight, price, shape, color, taste,
                                           pred1_label, pred1_proba, model1_data,
                                           pred2_label, top3_labels, top3_probas, model2_data)
        
        result_text.delete("1.0", tk.END)
        result_text.insert("1.0", result)
        
    except Exception as e:
        result_text.delete("1.0", tk.END)
        result_text.insert("1.0", f"❌ Ошибка при предсказании:\n{str(e)}")
        import traceback
        traceback.print_exc()

def generate_prediction_output(size, weight, price, shape, color, taste,
                               pred1_label, pred1_proba, model1_data,
                               pred2_label, top3_labels, top3_probas, model2_data):
    """Генерация текста результата предсказания"""
    result = ""
    result += "=" * 70 + "\n"
    result += "                    🔮 РЕЗУЛЬТАТ ПРЕДСКАЗАНИЯ\n"
    result += "=" * 70 + "\n\n"
    
    result += "📝 Входные данные:\n"
    result += f"   • Размер: {size} см\n"
    result += f"   • Вес: {weight} г\n"
    result += f"   • Цена: {price} ₹\n"
    result += f"   • Форма: {shape}\n"
    result += f"   • Цвет: {color}\n"
    result += f"   • Вкус: {taste}\n"
    
    result += "\n" + "─" * 70 + "\n"
    result += "🤖 MODEL 1: Binary Classification\n"
    result += "─" * 70 + "\n"
    result += f"   Тип: {pred1_label.upper()}\n"
    result += f"   Уверенность: {max(pred1_proba)*100:.2f}%\n"
    result += f"\n   Распределение вероятностей:\n"
    for i, cls in enumerate(model1_data['le_target'].classes_):
        bar_len = int(pred1_proba[i] * 40)
        bar = "█" * bar_len + "░" * (40 - bar_len)
        result += f"   {cls:12s} [{bar}] {pred1_proba[i]*100:5.2f}%\n"
    
    result += "\n" + "─" * 70 + "\n"
    result += "🤖 MODEL 2: Multi-class Classification\n"
    result += "─" * 70 + "\n"
    result += f"   Название: {pred2_label.upper()}\n"
    result += f"   Уверенность: {max(top3_probas)*100:.2f}%\n"
    result += f"\n   Топ-3 предсказания:\n"
    for i, (label, proba) in enumerate(zip(top3_labels, top3_probas), 1):
        bar_len = int(proba * 40)
        bar = "█" * bar_len + "░" * (40 - bar_len)
        result += f"   {i}. {label:15s} [{bar}] {proba*100:5.2f}%\n"
    
    result += "\n" + "=" * 70 + "\n"
    result += f"                    ✅ Итог: {pred2_label.upper()}\n"
    result += "=" * 70 + "\n"
    
    return result

def create_history_tab(notebook):
    """Создание вкладки истории предсказаний"""
    if not os.path.exists('predictions_results.json'):
        return
    
    history_frame = tk.Frame(notebook)
    notebook.add(history_frame, text="📜 История")
    
    history_scroll = tk.Scrollbar(history_frame)
    history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    history_text = tk.Text(history_frame, wrap=tk.WORD, 
                          yscrollcommand=history_scroll.set,
                          font=("Courier", 10), bg="#f5f5f5")
    history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    history_scroll.config(command=history_text.yview)
    
    try:
        with open('predictions_results.json', 'r', encoding='utf-8') as f:
            predictions = json.load(f)
        
        history_output = ""
        history_output += "=" * 80 + "\n"
        history_output += " " * 25 + "📜 ИСТОРИЯ ПРЕДСКАЗАНИЙ\n"
        history_output += "=" * 80 + "\n\n"
        history_output += f"Всего предсказаний: {len(predictions)}\n\n"
        
        for i, pred in enumerate(predictions[:20], 1):
            history_output += f"─── Предсказание #{i} {'─' * 60}\n"
            inp = pred['input']
            history_output += f"Input: {inp['color']} {inp['shape']}, {inp['size']} см, {inp['weight']} г\n"
            
            m1 = pred['predictions']['model1']
            history_output += f"Model1: {m1['type']} ({m1['confidence']*100:.1f}%)\n"
            
            m2 = pred['predictions']['model2']
            history_output += f"Model2: {m2['name']} ({m2['confidence']*100:.1f}%)\n"
            
            if 'actual' in pred:
                history_output += f"Actual: {pred['actual']['name']}"
                if pred.get('correct', {}).get('model2'):
                    history_output += " ✅\n"
                else:
                    history_output += " ❌\n"
            
            history_output += "\n"
        
        history_text.insert("1.0", history_output)
        history_text.config(state=tk.DISABLED)
        
    except Exception as e:
        history_text.insert("1.0", f"❌ Ошибка загрузки истории:\n{str(e)}")
        history_text.config(state=tk.DISABLED)