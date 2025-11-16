from utils.data_builder import load_base_dataset, to_csv_string
from config.paths import add_project_to_syspath

add_project_to_syspath()

from Client.Plugins.Text_Preprocesare import (  # type: ignore
    Plugin_Text_Cleaner as cleaner,
    Plugin_Tokenizer as tokenizer,
    Plugin_Lemmatizer as lemmatizer,
)


def _prepare_base_csv(limit=50):
    df = load_base_dataset(limit=limit)
    return to_csv_string(df)


def test_cleaner():
    csv_data = _prepare_base_csv()
    cleaner.base.csv_data = csv_data
    msg, outcsv = cleaner.do_work()

    assert "Ошибка" not in msg
    assert outcsv is not None
    assert "cleaned_text" in outcsv


def test_tokenizer():
    csv_data = _prepare_base_csv()
    cleaner.base.csv_data = csv_data
    _, cleaned = cleaner.do_work()

    tokenizer.base.csv_data = cleaned
    msg, outcsv = tokenizer.do_work()

    assert "Ошибка" not in msg
    assert outcsv is not None
    assert "tokens" in outcsv


def test_lemmatizer_not_crash():
    csv_data = _prepare_base_csv()
    cleaner.base.csv_data = csv_data
    _, cleaned = cleaner.do_work()

    tokenizer.base.csv_data = cleaned
    _, tokenized = tokenizer.do_work()

    lemmatizer.base.csv_data = tokenized
    msg, outcsv = lemmatizer.do_work()

    assert "Ошибка" not in msg
    assert outcsv is not None
