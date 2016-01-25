import os
import sys
from tools.calibration.calibtool.calibration_manager import run
# Add the dtk package locally
sys.path.insert(0,"C:\\Users\\braybaud\\PycharmProjects\\dtk-tools")
run('calibration_overlays.json')