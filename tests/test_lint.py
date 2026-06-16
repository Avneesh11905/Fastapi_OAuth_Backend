import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent

def test_ruff():
    result = subprocess.run([sys.executable, "-m", "ruff", "check", "."], cwd=BACKEND_DIR, capture_output=True, text=True)
    assert result.returncode == 0, f"Ruff failed:\n{result.stdout}\n{result.stderr}"

def test_mypy():
    result = subprocess.run([sys.executable, "-m", "mypy", ".", "--check-untyped-defs"], cwd=BACKEND_DIR, capture_output=True, text=True)
    assert result.returncode == 0, f"Mypy failed:\n{result.stdout}\n{result.stderr}"
