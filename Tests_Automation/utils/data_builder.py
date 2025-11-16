import pandas as pd
from io import StringIO
from config.paths import DATA_PATH, add_project_to_syspath


def load_base_dataset(limit: int | None = None) -> pd.DataFrame:
    """
    Încarcă dataset-ul original din proiectul principal.
    Opțional poate limita numărul de rânduri.
    """
    add_project_to_syspath()
    df = pd.read_csv(DATA_PATH)

    if limit is not None and limit < len(df):
        df = df.sample(n=limit, random_state=42).reset_index(drop=True)

    return df


def build_dataset_for_models(limit: int | None = None) -> pd.DataFrame:
    """
    Construcţie dataset pentru ambele modele:
    - adaugă coloana 'model_target'
    - 'model1' pentru clasificarea fruit/vegetable
    - 'model2' pentru clasificarea numelui (name)
    """
    df = load_base_dataset(limit=limit)

    # împărţim aproximativ jumătate / jumătate între model1 şi model2
    n = len(df)
    half = n // 2
    df = df.copy()
    df["model_target"] = "model1"
    if half > 0:
        df.loc[half:, "model_target"] = "model2"

    return df


def to_csv_string(df: pd.DataFrame) -> str:
    """
    Converteşte un DataFrame în string CSV pentru a fi trimis la plugin-uri.
    """
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()
