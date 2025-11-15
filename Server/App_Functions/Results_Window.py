from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QTextEdit, QLabel, QPushButton, QLineEdit, QComboBox,
                             QMessageBox, QFrame, QScrollArea, QGridLayout, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor
from datetime import datetime
import io
import pickle
import os
import json
import pandas as pd
import numpy as np

# Исправленный импорт - используем относительный импорт
from .CSV_Manager import get_current_csv_data


def show_results_window():
    """Интерактивное окно с результатами и возможностью делать предсказания"""
    current_csv_data = get_current_csv_data()

    if not current_csv_data:
        QMessageBox.information(None, "Инфо", "Нет данных для отображения")
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
        results_window = ResultsWindow(df, model1_data, model2_data)
        results_window.show()

        # ВАЖНО: Сохраняем ссылку на окно, чтобы оно не закрылось
        if not hasattr(show_results_window, '_windows'):
            show_results_window._windows = []
        show_results_window._windows.append(results_window)

    except Exception as e:
        QMessageBox.critical(None, "Ошибка", f"Не удалось отобразить результаты:\n{e}")
        import traceback
        traceback.print_exc()


class ResultsWindow(QWidget):
    def __init__(self, df, model1_data, model2_data):
        super().__init__()
        self.df = df
        self.model1_data = model1_data
        self.model2_data = model2_data

        self.setWindowTitle("🤖 AI Models Dashboard")
        self.setGeometry(100, 100, 1000, 750)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3d3d3d;
                color: #ffffff;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
        """)

        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        title_label = QLabel("🤖 AI Models Dashboard")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
            padding: 15px;
            background-color: #2b2b2b;
            border-radius: 10px;
            margin-bottom: 10px;
        """)
        main_layout.addWidget(title_label)

        # Notebook для вкладок
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #4CAF50;
            }
        """)

        # Создаём вкладки
        self.create_stats_tab()
        self.create_predictions_tab()
        self.create_history_tab()

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def create_stats_tab(self):
        """Создание вкладки статистики"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout()

        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        stats_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New';
                font-size: 11px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        # Генерируем статистику
        output = self.generate_stats_output()
        stats_text.setPlainText(output)

        stats_layout.addWidget(stats_text)
        stats_widget.setLayout(stats_layout)

        self.tab_widget.addTab(stats_widget, "📊 Статистика")

    def generate_stats_output(self):
        """Генерация текста статистики"""
        output = ""
        output += "=" * 80 + "\n"
        output += " " * 25 + "🎉 РЕЗУЛЬТАТЫ ОБУЧЕНИЯ 🎉\n"
        output += "=" * 80 + "\n\n"

        output += f"📂 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += f"📊 Всего записей: {len(self.df):,}\n"
        output += f"📋 Колонок: {len(self.df.columns)}\n\n"

        # Статистика предобработки
        output += "─" * 80 + "\n"
        output += "📝 ПРЕДОБРАБОТКА ДАННЫХ\n"
        output += "─" * 80 + "\n"

        if 'cleaned_text' in self.df.columns:
            output += f"✅ Text Cleaning: {self.df['cleaned_text'].notna().sum():,} записей\n"
        if 'tokens' in self.df.columns:
            output += f"✅ Tokenization: {self.df['tokens'].notna().sum():,} записей\n"
        if 'lemmas' in self.df.columns:
            output += f"✅ Lemmatization: {self.df['lemmas'].notna().sum():,} записей\n"

        if 'model_target' in self.df.columns:
            m1 = len(self.df[self.df['model_target'] == 'model1'])
            m2 = len(self.df[self.df['model_target'] == 'model2'])
            output += f"\n📊 Разделение данных:\n"
            output += f"   • Model 1 (Binary): {m1:,} ({m1 / len(self.df) * 100:.1f}%)\n"
            output += f"   • Model 2 (Multi-class): {m2:,} ({m2 / len(self.df) * 100:.1f}%)\n"

        output += "\n" + "─" * 80 + "\n"
        output += "🤖 МОДЕЛЬ 1: BINARY CLASSIFICATION (Decision Tree)\n"
        output += "─" * 80 + "\n"

        if self.model1_data:
            output += f"📈 Обучение:\n"
            output += f"   • Train Accuracy: {self.model1_data['train_acc']:.4f} ({self.model1_data['train_acc'] * 100:.2f}%)\n"
            output += f"   • Test Accuracy:  {self.model1_data['test_acc']:.4f} ({self.model1_data['test_acc'] * 100:.2f}%)\n"
            output += f"   • Train Size: {self.model1_data['train_size']:,} samples\n"
            output += f"   • Test Size:  {self.model1_data['test_size']:,} samples\n"
            output += f"   • Classes: {', '.join(self.model1_data['classes'])}\n"

            if 'model1_val_accuracy' in self.df.columns:
                val_acc = self.df['model1_val_accuracy'].iloc[0]
                cv_mean = self.df.get('model1_cv_mean', pd.Series([0])).iloc[0]
                output += f"\n📊 Валидация:\n"
                output += f"   • Validation Accuracy: {val_acc:.4f} ({val_acc * 100:.2f}%)\n"
                output += f"   • Cross-Validation: {cv_mean:.4f} ({cv_mean * 100:.2f}%)\n"
        else:
            output += "❌ Модель не обучена\n"

        output += "\n" + "─" * 80 + "\n"
        output += "🤖 МОДЕЛЬ 2: MULTI-CLASS CLASSIFICATION (Random Forest)\n"
        output += "─" * 80 + "\n"

        if self.model2_data:
            output += f"📈 Обучение:\n"
            output += f"   • Train Accuracy: {self.model2_data['train_acc']:.4f} ({self.model2_data['train_acc'] * 100:.2f}%)\n"
            output += f"   • Test Accuracy:  {self.model2_data['test_acc']:.4f} ({self.model2_data['test_acc'] * 100:.2f}%)\n"
            output += f"   • Train Size: {self.model2_data['train_size']:,} samples\n"
            output += f"   • Test Size:  {self.model2_data['test_size']:,} samples\n"
            output += f"   • Number of Classes: {self.model2_data['n_classes']}\n"

            if 'feature_importance' in self.model2_data:
                top_features = sorted(self.model2_data['feature_importance'].items(),
                                      key=lambda x: x[1], reverse=True)[:5]
                output += f"\n📊 Top 5 Features:\n"
                for feat, imp in top_features:
                    output += f"   • {feat}: {imp:.4f}\n"

            if 'model2_val_accuracy' in self.df.columns:
                val_acc = self.df['model2_val_accuracy'].iloc[0]
                cv_mean = self.df.get('model2_cv_mean', pd.Series([0])).iloc[0]
                output += f"\n📊 Валидация:\n"
                output += f"   • Validation Accuracy: {val_acc:.4f} ({val_acc * 100:.2f}%)\n"
                output += f"   • Cross-Validation: {cv_mean:.4f} ({cv_mean * 100:.2f}%)\n"
        else:
            output += "❌ Модель не обучена\n"

        output += "\n" + "=" * 80 + "\n"
        output += " " * 20 + "✨ МОДЕЛИ ГОТОВЫ К ИСПОЛЬЗОВАНИЮ ✨\n"
        output += "=" * 80 + "\n"

        return output

    def create_predictions_tab(self):
        """Создание вкладки предсказаний"""
        predict_widget = QWidget()
        predict_widget.setStyleSheet("background-color: #2b2b2b;")
        predict_layout = QVBoxLayout()

        # Заголовок
        title_label = QLabel("🔮 Тестирование моделей")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            background-color: #4CAF50;
            padding: 15px;
            border-radius: 10px;
        """)
        predict_layout.addWidget(title_label)

        # Форма ввода
        input_group = QGroupBox("📝 Входные параметры")
        input_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #4CAF50;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 5px;
            }
        """)

        input_layout = QGridLayout()
        input_layout.setSpacing(15)
        input_layout.setContentsMargins(20, 25, 20, 20)

        # Получаем уникальные значения
        unique_shapes = self.df['shape'].unique().tolist() if 'shape' in self.df.columns else []
        unique_colors = self.df['color'].unique().tolist() if 'color' in self.df.columns else []
        unique_tastes = self.df['taste'].unique().tolist() if 'taste' in self.df.columns else []

        # Стиль для меток и полей
        label_style = """
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
            }
        """

        input_style = """
            QLineEdit, QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 2px solid #505050;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #4CAF50;
                margin-right: 10px;
            }
        """

        # Поля ввода
        self.fields = {}

        row = 0
        label = QLabel("Размер (см):")
        label.setStyleSheet(label_style)
        self.size_entry = QLineEdit("5.0")
        self.size_entry.setStyleSheet(input_style)
        input_layout.addWidget(label, row, 0)
        input_layout.addWidget(self.size_entry, row, 1)
        self.fields['size'] = self.size_entry

        row += 1
        label = QLabel("Вес (г):")
        label.setStyleSheet(label_style)
        self.weight_entry = QLineEdit("150")
        self.weight_entry.setStyleSheet(input_style)
        input_layout.addWidget(label, row, 0)
        input_layout.addWidget(self.weight_entry, row, 1)
        self.fields['weight'] = self.weight_entry

        row += 1
        label = QLabel("Цена (₹):")
        label.setStyleSheet(label_style)
        self.price_entry = QLineEdit("50")
        self.price_entry.setStyleSheet(input_style)
        input_layout.addWidget(label, row, 0)
        input_layout.addWidget(self.price_entry, row, 1)
        self.fields['price'] = self.price_entry

        row += 1
        label = QLabel("Форма:")
        label.setStyleSheet(label_style)
        self.shape_combo = QComboBox()
        self.shape_combo.addItems(unique_shapes)
        self.shape_combo.setStyleSheet(input_style)
        input_layout.addWidget(label, row, 0)
        input_layout.addWidget(self.shape_combo, row, 1)
        self.fields['shape'] = self.shape_combo

        row += 1
        label = QLabel("Цвет:")
        label.setStyleSheet(label_style)
        self.color_combo = QComboBox()
        self.color_combo.addItems(unique_colors)
        self.color_combo.setStyleSheet(input_style)
        input_layout.addWidget(label, row, 0)
        input_layout.addWidget(self.color_combo, row, 1)
        self.fields['color'] = self.color_combo

        row += 1
        label = QLabel("Вкус:")
        label.setStyleSheet(label_style)
        self.taste_combo = QComboBox()
        self.taste_combo.addItems(unique_tastes)
        self.taste_combo.setStyleSheet(input_style)
        input_layout.addWidget(label, row, 0)
        input_layout.addWidget(self.taste_combo, row, 1)
        self.fields['taste'] = self.taste_combo

        input_group.setLayout(input_layout)
        predict_layout.addWidget(input_group)

        # Кнопка предсказания
        predict_btn = QPushButton("🔮 Сделать предсказание")
        predict_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        predict_btn.clicked.connect(self.make_prediction)
        predict_layout.addWidget(predict_btn)

        # Результат
        result_group = QGroupBox("📊 Результаты предсказания")
        result_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #4CAF50;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 5px;
            }
        """)

        result_layout = QVBoxLayout()
        result_layout.setContentsMargins(15, 20, 15, 15)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New';
                font-size: 11px;
                border: 2px solid #505050;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        self.result_text.setMinimumHeight(250)

        result_layout.addWidget(self.result_text)
        result_group.setLayout(result_layout)
        predict_layout.addWidget(result_group)

        predict_widget.setLayout(predict_layout)
        self.tab_widget.addTab(predict_widget, "🔮 Предсказания")

    def make_prediction(self):
        """Функция предсказания"""
        if not self.model1_data or not self.model2_data:
            self.result_text.setPlainText("❌ Модели не обучены! Сначала запустите обучение.")
            return

        try:
            # Получаем данные из полей
            size = float(self.size_entry.text())
            weight = float(self.weight_entry.text())
            price = float(self.price_entry.text())
            shape = self.shape_combo.currentText()
            color = self.color_combo.currentText()
            taste = self.taste_combo.currentText()

            # === ПРЕДСКАЗАНИЕ MODEL 1 (Binary) ===
            X1_data = {
                'size (cm)': [size],
                'weight (g)': [weight],
                'avg_price (₹)': [price]
            }

            # Кодируем категориальные признаки для Model1
            for col in ['shape', 'color', 'taste']:
                le = self.model1_data['le_dict'][col]
                val = {'shape': shape, 'color': color, 'taste': taste}[col]
                if val in le.classes_:
                    encoded = le.transform([val])[0]
                else:
                    encoded = 0
                X1_data[f'{col}_encoded'] = [encoded]

            X1_sample = pd.DataFrame(X1_data)
            X1_sample = X1_sample[self.model1_data['feature_cols']]

            pred1_encoded = self.model1_data['model'].predict(X1_sample)[0]
            pred1_label = self.model1_data['le_target'].inverse_transform([pred1_encoded])[0]
            pred1_proba = self.model1_data['model'].predict_proba(X1_sample)[0]

            # === ПРЕДСКАЗАНИЕ MODEL 2 (Multi-class) ===
            X2_data = {
                'size (cm)': [size],
                'weight (g)': [weight],
                'avg_price (₹)': [price]
            }

            for col in ['shape', 'color', 'taste', 'type']:
                le = self.model2_data['le_dict'][col]
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
            X2_sample = X2_sample[self.model2_data['feature_cols']]

            pred2_encoded = self.model2_data['model'].predict(X2_sample)[0]
            pred2_label = self.model2_data['le_target'].inverse_transform([pred2_encoded])[0]
            pred2_proba = self.model2_data['model'].predict_proba(X2_sample)[0]

            # Топ-3 предсказания для Model2
            top3_indices = np.argsort(pred2_proba)[-3:][::-1]
            top3_labels = self.model2_data['le_target'].inverse_transform(top3_indices)
            top3_probas = pred2_proba[top3_indices]

            # Формируем результат
            result = self.generate_prediction_output(
                size, weight, price, shape, color, taste,
                pred1_label, pred1_proba,
                pred2_label, top3_labels, top3_probas
            )

            self.result_text.setPlainText(result)

        except Exception as e:
            self.result_text.setPlainText(f"❌ Ошибка при предсказании:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def generate_prediction_output(self, size, weight, price, shape, color, taste,
                                   pred1_label, pred1_proba,
                                   pred2_label, top3_labels, top3_probas):
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
        result += f"   Уверенность: {max(pred1_proba) * 100:.2f}%\n"
        result += f"\n   Распределение вероятностей:\n"
        for i, cls in enumerate(self.model1_data['le_target'].classes_):
            bar_len = int(pred1_proba[i] * 40)
            bar = "█" * bar_len + "░" * (40 - bar_len)
            result += f"   {cls:12s} [{bar}] {pred1_proba[i] * 100:5.2f}%\n"

        result += "\n" + "─" * 70 + "\n"
        result += "🤖 MODEL 2: Multi-class Classification\n"
        result += "─" * 70 + "\n"
        result += f"   Название: {pred2_label.upper()}\n"
        result += f"   Уверенность: {max(top3_probas) * 100:.2f}%\n"
        result += f"\n   Топ-3 предсказания:\n"
        for i, (label, proba) in enumerate(zip(top3_labels, top3_probas), 1):
            bar_len = int(proba * 40)
            bar = "█" * bar_len + "░" * (40 - bar_len)
            result += f"   {i}. {label:15s} [{bar}] {proba * 100:5.2f}%\n"

        result += "\n" + "=" * 70 + "\n"
        result += f"                    ✅ Итог: {pred2_label.upper()}\n"
        result += "=" * 70 + "\n"

        return result

    def create_history_tab(self):
        """Создание вкладки истории предсказаний"""
        if not os.path.exists('predictions_results.json'):
            return

        history_widget = QWidget()
        history_layout = QVBoxLayout()

        history_text = QTextEdit()
        history_text.setReadOnly(True)
        history_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New';
                font-size: 11px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
        """)

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
                history_output += f"Model1: {m1['type']} ({m1['confidence'] * 100:.1f}%)\n"

                m2 = pred['predictions']['model2']
                history_output += f"Model2: {m2['name']} ({m2['confidence'] * 100:.1f}%)\n"

                if 'actual' in pred:
                    history_output += f"Actual: {pred['actual']['name']}"
                    if pred.get('correct', {}).get('model2'):
                        history_output += " ✅\n"
                    else:
                        history_output += " ❌\n"

                history_output += "\n"

            history_text.setPlainText(history_output)

        except Exception as e:
            history_text.setPlainText(f"❌ Ошибка загрузки истории:\n{str(e)}")

        history_layout.addWidget(history_text)
        history_widget.setLayout(history_layout)

        self.tab_widget.addTab(history_widget, "📜 История")