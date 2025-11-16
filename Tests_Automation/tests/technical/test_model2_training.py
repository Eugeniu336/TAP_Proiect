from utils.data_builder import build_dataset_for_models, to_csv_string
from config.paths import add_project_to_syspath

add_project_to_syspath()

from Client.Plugins.Model_Antrenare import Plugin_Antrenare_Model2 as model2_train  # type: ignore


def test_model2_training():
    df = build_dataset_for_models(limit=300)
    df_model2 = df[df["model_target"] == "model2"]
    csv_data = to_csv_string(df_model2)

    model2_train.base.csv_data = csv_data
    msg, outcsv = model2_train.do_work()

    # pentru unele subseturi foarte mici stratify poate da eroare;
    # în proiectul real aveai xfail; aici mergem pe așteptare de succes
    assert "Ошибка" not in msg
    assert outcsv is not None
    assert "model2_trained" in outcsv
