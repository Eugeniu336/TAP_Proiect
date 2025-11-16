"""
PLUGIN 3: Lemmatizer & Splitter
Уровень: 3, Режим: Последовательно
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Client/Client_Template')))
import Client_Template as base

base.CLIENT_NAME = "Lemmatizer"
base.CLIENT_LEVEL = "3"
base.CLIENT_MODE = "Sequential"

LEMMA_DICT = {
    "products": "product", "services": "service", "phones": "phone",
    "loves": "love", "batteries": "battery", "lives": "life",
    "screens": "screen", "disappointed": "disappoint", 
    "purchases": "purchase", "needed": "need",
    "apples": "apple", "bananas": "banana", "oranges": "orange"
}

def do_work():
    import pandas as pd
    import io
    import ast
    
    csv_data = base.csv_data
    
    if not csv_data:
        return "Error: CSV data not received", None
    
    try:
        df = pd.read_csv(io.StringIO(csv_data))
        
        if 'tokens' not in df.columns:
            return f"Error: Column 'tokens' not found. Available: {list(df.columns)}", None
        
        # Преобразуем строку обратно в список
        df['tokens'] = df['tokens'].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else []
        )
        
        # Применяем лемматизацию
        df['lemmas'] = df['tokens'].apply(
            lambda tokens: [LEMMA_DICT.get(t, t) for t in tokens] if isinstance(tokens, list) else []
        )
        
        # ===== РАЗДЕЛЕНИЕ НА 2 ЧАСТИ =====
        # Перемешиваем данные
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Делим пополам
        mid_point = len(df) // 2
        
        # Часть 1 для Model1 (binary classification: fruit vs vegetable)
        df1 = df.iloc[:mid_point].copy()
        df1['model_target'] = 'model1'
        
        # Часть 2 для Model2 (multi-class: predict name)
        df2 = df.iloc[mid_point:].copy()
        df2['model_target'] = 'model2'
        
        # Объединяем обратно
        df_final = pd.concat([df1, df2], ignore_index=True)
        
        result_csv = df_final.to_csv(index=False)
        result_msg = f"Lemmatizer: Lemmatized {len(df)} rows. Split: Model1={len(df1)}, Model2={len(df2)}"
        
        return result_msg, result_csv
        
    except Exception as e:
        return f"Lemmatizer: Error - {str(e)}", None

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()