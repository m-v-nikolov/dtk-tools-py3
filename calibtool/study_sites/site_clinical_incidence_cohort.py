from site_setup_functions import *


fine_age_bins = [
    0.08333, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 20, 25, 30, 40, 50, 60, 100
]


setup_functions = [
    config_setup_fn(duration=21915),  # 60 years (with leap years)
    summary_report_fn(age_bins=fine_age_bins, interval=360),  # TODO: reconcile with 365/12 monthly EIR functions

    # TODO: import this block as birth_cohort_setup from site_setup_functions
    lambda cb: cb.update_params({
        'Geography': 'Calibration',
        'Demographics_Filenames': ['Calibration/birth_cohort_demographics.compiled.json'],
        'Base_Population_Scale_Factor': 10,
        'Enable_Vital_Dynamics': 0,  # No births/deaths.  Just following a birth cohort.
        'Climate_Model': 'CLIMATE_CONSTANT'})
]


def get_setup_functions(site):
    setup_functions.append(site_input_eir_fn(site))
    return setup_functions
