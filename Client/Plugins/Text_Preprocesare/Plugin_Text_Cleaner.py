"""
PLUGIN 1: Text Cleaner
Уровень: 1, Режим: Последовательно
"""
import sys
import os
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../Client/Client_Template')))
import Client_Template as base

base.CLIENT_NAME = "Text_Cleaner"
base.CLIENT_LEVEL = "1"
base.CLIENT_MODE = "Sequential"

def do_work():
    import pandas as pd
    import io
    
    csv_data = base.csv_data
    
    if not csv_data:
        return "Error: CSV data not received", None
    
    df = pd.read_csv(io.StringIO(csv_data))
    
    # Ищем текстовую колонку (name)
    text_column = 'name' if 'name' in df.columns else None
    
    if text_column is None:
        return "Error: Column 'name' not found", None
    
    def clean_text(text):
        cleaned = str(text).lower()
        cleaned = re.sub(r'[^a-zA-Z\s]', '', cleaned)
        cleaned = ' '.join(cleaned.split())
        return cleaned
    
    df['cleaned_text'] = df[text_column].apply(clean_text)
    
    result_csv = df.to_csv(index=False)
    result_msg = f"Text_Cleaner: Processed {len(df)} rows"
    
    return result_msg, result_csv

base.do_work = do_work

if __name__ == "__main__":
    base.create_gui()