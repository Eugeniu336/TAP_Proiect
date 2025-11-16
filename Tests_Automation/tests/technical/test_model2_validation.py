from utils.data_builder import build_dataset_for_models, to_csv_string
from config.paths import add_project_to_syspath

add_project_to_syspath()

from Client.Plugins.Model_Antrenare import (
    Plugin_Antrenare_Model2 as model2_train,    # type: ignore
    Plugin_Validare_Model2 as model2_val,       # type: ignore
)


def test_model2_validation():
    df = build_dataset_for_models(limit=300)
    df_model2 = df[df["model_target"] == "model2"]
    csv_data = to_csv_string(df_model2)

    model2_train.base.csv_data = csv_data
    msg_train, trained_csv = model2_train.do_work()

    assert "Ошибка" not in msg_train
    assert trained_csv is not None

    model2_val.base.csv_data = trained_csv
    msg_val, outcsv = model2_val.do_work()

    assert "Ошибка" not in msg_val
    assert outcsv is not None
    assert "model2_validated" in outcsv
