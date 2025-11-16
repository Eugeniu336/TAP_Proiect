from pathlib import Path

# <<< ADAPTEAZĂ dacă se schimbă locația proiectului colegilor >>>
PROJECT_ROOT = Path(
    r"C:\Users\adria\OneDrive\Рабочий стол\Tap_proiect\TAP_Proiect"
)

CLIENT_ROOT = PROJECT_ROOT / "Client"
SERVER_ROOT = PROJECT_ROOT / "Server"
DATA_PATH = PROJECT_ROOT / "data" / "fruit_vegetable_classification_dataset.csv"

# pentru importuri directe din proiectul principal
def add_project_to_syspath():
    """
    Adaugă proiectul principal în sys.path ca să putem importa:
    - Client.Client_Template.Client_Template
    - Client.Plugins.Model_Antrenare.Plugin_Antrenare_Model1, etc.
    """
    import sys
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
