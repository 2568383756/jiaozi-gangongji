"""Compatibility entry: always build the approved solid-hand final version."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("build_solid_hand_characters.py")), run_name="__main__")
