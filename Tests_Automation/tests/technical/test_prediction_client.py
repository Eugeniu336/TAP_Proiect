from utils.data_builder import build_dataset_for_models, to_csv_string
from config.paths import add_project_to_syspath

add_project_to_syspath()

from Client.Plugins.Model_Antrenare import (
    Plugin_Antrenare_Model1 as model1_train,   # type: ignore
    Plugin_Antrenare_Model2 as model2_train,   # type: ignore
)
from Client.Plugins.Model_Antrenare import Plugin_Prediction_Client as pred_client  # type: ignore


def test_prediction_client_runs():
    df = build_dataset_for_models(limit=200)
    csv_data = to_csv_string(df)

    # train both models
    model1_train.base.csv_data = csv_data
    _, trained1 = model1_train.do_work()

    model2_train.base.csv_data = trained1
    _, trained2 = model2_train.do_work()

    # prediction client
    pred_client.base.csv_data = trained2
    msg, outcsv = pred_client.do_work()

    assert "Ошибка" not in msg
    assert outcsv is not None
    assert "prediction_result" in outcsv or "predicted" in outcsv or "prob" in outcsv
