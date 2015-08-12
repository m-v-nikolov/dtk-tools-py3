Running outside Edward's python tools
-------------------------------------

Modify run_one_simulation() in calibration_manager.py appropriately
for new method of running sims. If you're running outside the python
tools, it's likely you're using new sites and analyzers, so update
geographies and initial parameter sampling files as well as
load_settings.py, load_comparison_data.py, analyzers.py, and
visualize.py accordingly. If IMIS is still being used, there is no
need to modify next_parameters.py as long as analyzer output continues
to be stored in the same format.
