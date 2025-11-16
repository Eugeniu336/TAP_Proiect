import subprocess
import sys
import re
from dataclasses import dataclass

# =====================================================================
#  STRUCTURĂ DATE PENTRU REZULTATE
# =====================================================================

@dataclass
class TestCategoryResult:
    name: str
    passed: list
    failed: list
    errors: list
    skipped: list
    exit_code: int
    raw_stdout: str
    raw_stderr: str


# =====================================================================
#  PARSARE OUTPUT PYTEST
# =====================================================================

def parse_pytest_output(output: str):
    passed = re.findall(r"(\S+)\s+PASSED", output)
    failed = re.findall(r"(\S+)\s+FAILED", output)
    skipped = re.findall(r"(\S+)\s+SKIPPED", output)
    errors = re.findall(r"(\S+)\s+ERROR", output)

    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
    }


# =====================================================================
#  EXECUTARE PYTEST CU SUPORT COMPLET OUTPUT
# =====================================================================

def run_pytest(category_name: str, test_path: str) -> TestCategoryResult:
    python_cmd = sys.executable

    cmd = [
        python_cmd,
        "-m", "pytest",
        test_path,
        "-rA",                 # arată toate testele PASSED/FAILED/SKIPPED
        "--maxfail=0",
        "--disable-warnings",
        "--capture=no",        # IMPORTANT: fără asta PyQt blochează stdout
        "-q",                  # output compact (dar vizibil)
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    parsed = parse_pytest_output(stdout)

    return TestCategoryResult(
        name=category_name,
        passed=parsed["passed"],
        failed=parsed["failed"],
        errors=parsed["errors"],
        skipped=parsed["skipped"],
        exit_code=result.returncode,
        raw_stdout=stdout,
        raw_stderr=stderr,
    )


# =====================================================================
#  PRINTARE FRUMOASĂ REZULTATE
# =====================================================================

def print_category_details(category: TestCategoryResult):
    print(f"\n🔷 {category.name}")

    if category.passed:
        print("   ✔ Passed:")
        for t in category.passed:
            print(f"      • {t}")
    else:
        print("   ✔ Passed: — nimic —")

    if category.failed:
        print("   ❌ Failed:")
        for t in category.failed:
            print(f"      • {t}")
    else:
        print("   ❌ Failed: — nimic —")

    if category.errors:
        print("   ⚠ Errors:")
        for t in category.errors:
            print(f"      • {t}")
    else:
        print("   ⚠ Errors: — nimic —")

    if category.skipped:
        print("   ⏭ Skipped:")
        for t in category.skipped:
            print(f"      • {t}")
    else:
        print("   ⏭ Skipped: — nimic —")

    print(f"   🔚 Exit Code: {category.exit_code}")


def print_summary_table(results):
    print("┌──────────────────────────── ✔ Rezultate Finale ─────────────────────────────┐")
    print("│                              📊 Rezumat Teste                               │")
    print("│ ┌─────────────────────────────┬────────┬────────┬────────┬─────────┬──────┐ │")
    print("│ │ Categoria                   │ Passed │ Failed │ Errors │ Skipped │ Exit │ │")
    print("│ ├─────────────────────────────┼────────┼────────┼────────┼─────────┼──────┤ │")

    for r in results:
        print(f"│ │ {r.name:<27} │ {len(r.passed):<6} │ {len(r.failed):<6} │ {len(r.errors):<6} │ {len(r.skipped):<7} │ {r.exit_code:<4} │ │")

    print("│ └─────────────────────────────┴────────┴────────┴────────┴─────────┴──────┘ │")
    print("└─────────────────────────────────────────────────────────────────────────────┘")


# =====================================================================
#  MAIN EXECUTION
# =====================================================================

if __name__ == "__main__":

    print("\n══════════════════════════════════")
    print("   🚀 RULARE COMPLETĂ TESTE")
    print("══════════════════════════════════\n")

    results = []

    print("\n🔎 Rulez testele: Technical...")
    tech = run_pytest("Technical", "tests/technical")
    print("✔ Testele «Technical» au fost finalizate.\n")
    results.append(tech)

    print("\n🔎 Rulez testele: Functional...")
    func = run_pytest("Functional", "tests/functional")
    print("✔ Testele «Functional» au fost finalizate.\n")
    results.append(func)

    print("\n🔎 Rulez testele: Advanced...")
    adv = run_pytest("Advanced", "tests/functional/advanced")
    print("✔ Testele «Advanced» au fost finalizate.\n")
    results.append(adv)

    # TABEL FINAL
    print_summary_table(results)

    # DETALII TESTE
    print("\n══════════════════════════════════════════════════════════════════")
    print("                        📄 DETALII TESTE")
    print("══════════════════════════════════════════════════════════════════\n")

    for r in results:
        print_category_details(r)

    print("\n✔ RULARE COMPLETĂ FINALIZATĂ\n")
