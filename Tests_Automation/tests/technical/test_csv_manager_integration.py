import sys
from pathlib import Path

from config.paths import SERVER_ROOT, DATA_PATH, add_project_to_syspath
add_project_to_syspath()

from Server.App_Functions import CSV_Manager as csvm  # type: ignore


def test_csv_manager_loads_initial_file():
    csv_data, csv_file = csvm.load_initial_csv()

    assert csv_data is not None
    assert csv_file is not None

    assert Path(csv_file).name == DATA_PATH.name
    assert "," in csv_data  # CSV text
    assert "size (cm)" in csv_data
