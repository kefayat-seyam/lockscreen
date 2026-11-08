import sys

print("LinkScreen environment check")
print("=" * 32)
print("Python executable:", sys.executable)
print("Python version:", sys.version)

if sys.version_info < (3, 15):
    raise SystemExit("ERROR: LinkScreen requires Python 3.15 or newer.")

try:
    import PySide6
    from PySide6.QtWidgets import QApplication
    print("PySide6:", PySide6.__version__)
except Exception as exc:
    raise SystemExit(f"ERROR: PySide6 import failed: {exc}")

try:
    import cryptography
    print("cryptography:", cryptography.__version__)
except Exception as exc:
    raise SystemExit(f"ERROR: cryptography import failed: {exc}")

print("\nSUCCESS: Windows development dependencies are importable.")
print("Next: run `python desktop/main.py`.")
