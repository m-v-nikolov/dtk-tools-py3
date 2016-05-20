from site_setup_functions import *

survey_day = 730
survey_interval=10000

setup_functions = [ config_setup_fn(duration=1461),
                    add_treatment_fn(),
                    survey_report_fn(days=[survey_day], interval=survey_interval),
                    lambda cb : cb.update_params( {  "Geography": "Burkina",
                                                    'Base_Population_Scale_Factor' : 1,
                                                    'Enable_Vital_Dynamics' : 0,
                                                    "Climate_Model" : "CLIMATE_CONSTANT"
                                                } ),
                    lambda cb: cb.update_params({'Demographic_Coverage' : 0.95,
                    'Base_Gametocyte_Production_Rate' : 0.1,
                    "Gametocyte_Stage_Survival_Rate": 0.58,
                    'Antigen_Switch_Rate' : 2.83e-10,
                    'Falciparum_PfEMP1_Variants' : 1114,
                    'Falciparum_MSP_Variants' : 42,
                    'MSP1_Merozoite_Kill_Fraction' : 0.46,
                    'Falciparum_Nonspecific_Types' : 46,
                    'Nonspecific_Antigenicity_Factor' : 0.32,
                    'Max_Individual_Infections' : 3})]
reference_data = {}

analyzers = {         'seasonal_infectiousness_analyzer' : { 'name' : 'analyze_seasonal_infectiousness',
                                                          'seasons' : { 'start_wet' : 6, 'peak_wet' : 8, 'end_wet' : 0},
                                                          'reporter' : 'Survey Report',
                                                         'start_day' : survey_day,
                                                         'interval' : survey_interval,
                                                         'fields_to_get' : ['infectiousness', 'true_gametocytes', 'initial_age'],
                                                         'reporter_output_tail' : str(survey_day) + '_-1',
                                                         'LL_fn' : 'dirichlet_multinomial'
                                                      }}

def get_setup_functions(site) :

    setup_functions.append(site_input_eir_fn(site,birth_cohort=False, set_site_geography=False))
    setup_functions.append(lambda cb : cb.update_params ( { "Demographics_Filenames" : ['Burkina/Burkina/Burkina Faso_' + site + '_2.5arcmin_demographics.static.compiled.json'] }))
    setup_functions.append(add_immunity_fn(['150113_calib9']))
    return setup_functions

def load_reference_data(datatype) :

    return reference_data[datatype]

def get_analyzers(analyzer) :

    return analyzers[analyzer]
