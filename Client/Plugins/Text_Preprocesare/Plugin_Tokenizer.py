"""
PLUGIN 2: Tokenizer
Уровень: 2, Режим: Последовательно
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Client/Client_Template')))
import Client_Template as base

base.CLIENT_NAME = "Tokenizer"
base.CLIENT_LEVEL = "2"
base.CLIENT_MODE = "Sequential"

def do_work():
    import pandas as pd
    import io
    
    csv_data = base.csv_data
    
    if not csv_data:
        return "Error: CSV data not received", None
    
    try:
        df = pd.read_csv(io.StringIO(csv_data))
        
        # Ищем колонку cleaned_text
        text_column = 'cleaned_text' if 'cleaned_text' in df.columns else 'name'
        
        if text_column not in df.columns:
            return f"Error: Column '{text_column}' not found. Available: {list(df.columns)}", None
        
        # Токенизация: разбиваем на слова длиной > 1
        df['tokens'] = df[text_column].apply(
            lambda x: [t for t in str(x).split() if len(t) > 1]
        )
        
        result_csv = df.to_csv(index=False)
        result_msg = f"Tokenizer: Tokenized {len(df)} rows"
        
        return result_msg, result_csv
        
    except Exception as e:
        return f"Tokenizer: Error - {str(e)}", None

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()