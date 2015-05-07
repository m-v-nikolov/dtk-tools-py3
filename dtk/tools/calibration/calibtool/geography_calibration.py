from dtk.interventions.malaria_challenge import add_challenge_trial
from dtk.interventions.malaria_drugs import add_drug_campaign
from dtk.interventions.health_seeking import add_health_seeking
from dtk.interventions.input_EIR import add_InputEIR
from dtk.utils.reports.report_manager import add_reports

def set_geography(cb, geography, geography_info, dll_root='') :
    set_geography_config(cb, geography, geography_info)
    set_geography_campaigns(cb, geography, geography_info)
    set_geography_reporters(cb, geography, geography_info, dll_root)
    return cb

def set_geography_config(cb, geography, geography_info):
    mod_params = geography_info[geography]["config"]
    cb.update_params(mod_params)

def set_geography_campaigns(cb, geography, geography_info):
    campaigns = geography_info[geography]["campaign"]
    if 'input EIR' in campaigns.keys() :
        add_InputEIR(cb, campaigns['input EIR']['EIRs'], start_day=campaigns['input EIR']['start_day'])
    if 'health seeking' in campaigns.keys() :
        add_health_seeking(cb, start_day=campaigns['health seeking']['start_day'], drug=campaigns['health seeking']['drugs'], 
                           targets=[{'trigger' : 'NewClinicalCase', 'coverage' : campaigns['health seeking']['coverage'], 
                                     'seek' : campaigns['health seeking']['seek'], 'rate' : campaigns['health seeking']['rate']}])
        cb.update_params({'PKPD_Model' : 'CONCENTRATION_VERSUS_TIME'})
    if 'challenge bite' in campaigns.keys() :
        add_challenge_trial(cb)
    return cb

def set_geography_reporters(cb, geography, geography_info, dll_root='') :
    add_reports(cb, dll_root, reports=geography_info[geography]["report"])
    return cb

def get_geography_settings(geography, geography_info, info_type="config") :
    return geography_info[geography][info_type]
