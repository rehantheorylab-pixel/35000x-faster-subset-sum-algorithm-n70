"""Path helper that finds repo root regardless of username."""
import os, sys

def get_repo_root():
    script = os.path.abspath(__file__)
    scripts_dir = os.path.dirname(script)
    return os.path.dirname(scripts_dir)

def get_zpp_py():
    return os.path.join(get_repo_root(), "Z++.py")

def get_zpp_exe():
    exe = os.path.join(get_repo_root(), "zpp_rust", "target", "release", "zpp.exe")
    if os.path.isfile(exe):
        return exe
    exe2 = os.path.join(get_repo_root(), "zpp.exe")
    if os.path.isfile(exe2):
        return exe2
    return None

def get_test_elements():
    return os.path.join(get_repo_root(), "jnh1.cnf", "z_test_elements.txt")

def get_gui_py():
    return os.path.join(get_repo_root(), "Z_plus_plus_gui.py")

REPO_ROOT = get_repo_root()
ZPP_PY = get_zpp_py()
ZPP_EXE = get_zpp_exe()
TEST_ELEMENTS = get_test_elements()
GUI_PY = get_gui_py()
