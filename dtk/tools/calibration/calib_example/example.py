# Add the current dtk dir to the path
import os
import sys
sys.path.insert(0, os.path.abspath("..\\..\\..\\.."))

# Add the dtk package locally
from tools.calibration.calibtool.calibration_manager import run
run('calibration_overlays.json')