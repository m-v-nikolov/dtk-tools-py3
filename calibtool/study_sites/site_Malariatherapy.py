from site_setup_functions import *

setup_functions = [ config_setup_fn(duration=730),
                    lambda cb: cb.update_params( {    "Geography": "Calibration",
                                                      "Demographics_Filename": "Calibration/Malariatherapy_demographics.compiled.json",
                                                      "Base_Population_Scale_Factor" : 2,
                                                      "Enable_Vital_Dynamics" : 0,
                                                      "Climate_Model" : "CLIMATE_CONSTANT" # no mosquitoes in challenge trial setting
                                                      } ),
                    add_challenge_trial,
                    survey_report_fn(days=[1])]

reference_data = {        "density_timecourse" : {
            "n_obs_densities" : 131,
            "parasitemia_bins" : [10, 100, 1000, 10000, 100000, 1e9],
            "peak_parasitemias" : [0, 0, 1, 14, 94, 22],
            "peak_gametocytemias" : [10, 22, 50, 45, 4, 0],
            "n_obs_durations" : 118,
            "infection_duration_bins" : [20, 50, 100, 150, 200, 300, 1000],
            "parasitemia_durations" : [4, 16, 33, 27, 14, 17, 7],
            "gametocytemia_durations" : [14, 36, 28, 15, 9, 14, 2]
        }
}

analyzers = {     'malariatherapy_density_analyzer' : { 'name' : 'analyze_malariatherapy_density',
                                                        'reporter' : 'Survey Report',
                                                        'reporter_output_tail' : '1_-1',
                                                        'fields_to_get' : ['true_asexual_parasites', 'true_gametocytes'],
                                                        'LL_fn' : 'dirichlet_single'
                                                    },
                  'malariatherapy_duration_analyzer' : { 'name' : 'analyze_malariatherapy_duration',
                                                        'reporter' : 'Survey Report',
                                                        'reporter_output_tail' : '1_-1',
                                                        'fields_to_get' : ['true_asexual_parasites', 'true_gametocytes'],
                                                        'LL_fn' : 'dirichlet_single'
                                                    }}

def get_setup_functions() :

    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return analyzers[analyzer]
