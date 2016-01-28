import sys
sys.path.insert(0,"C:\\Users\\braybaud\\PycharmProjects\\dtk-tools")

# Add the dtk package locally
from tools.calibration.calibtool.calibration_manager import run
run('calibration_overlays.json')