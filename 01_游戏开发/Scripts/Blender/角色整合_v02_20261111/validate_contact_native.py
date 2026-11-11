"""Compatibility entry: the final solid-hand validator supersedes pre-remesh tests."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('validate_solid_hand_native.py')), run_name='__main__')
