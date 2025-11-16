from utils.data_builder import build_dataset_for_models, to_csv_string
from config.paths import add_project_to_syspath

add_project_to_syspath()

from Client.Plugins.Model_Antrenare import (
    Plugin_Antrenare_Model1 as model1_train,   # type: ignore
    Plugin_Validare_Model1 as model1_val,      # type: ignore
)


def test_model1_validation():
    df = build_dataset_for_models(limit=200)
    df_model1 = df[df["model_target"] == "model1"]
    csv_data = to_csv_string(df_model1)

    model1_train.base.csv_data = csv_data
    msg_train, trained_csv = model1_train.do_work()

    assert "Ошибка" not in msg_train
    assert trained_csv is not None

    # rulăm validarea
    model1_val.base.csv_data = trained_csv
    msg_val, outcsv = model1_val.do_work()

    assert "Ошибка" not in msg_val
    assert outcsv is not None
    assert "model1_validated" in outcsv
