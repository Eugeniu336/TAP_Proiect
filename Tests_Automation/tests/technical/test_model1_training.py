from utils.data_builder import build_dataset_for_models, to_csv_string
from config.paths import add_project_to_syspath

add_project_to_syspath()

from Client.Plugins.Model_Antrenare import Plugin_Antrenare_Model1 as model1_train  # type: ignore


def test_model1_training():
    df = build_dataset_for_models(limit=200)
    # selectăm doar rândurile pentru model1
    df_model1 = df[df["model_target"] == "model1"]
    csv_data = to_csv_string(df_model1)

    model1_train.base.csv_data = csv_data
    msg, outcsv = model1_train.do_work()

    assert "Ошибка" not in msg
    assert outcsv is not None
    assert "model1_trained" in outcsv
