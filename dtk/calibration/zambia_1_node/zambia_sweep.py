## Execute from dtk.py script in malaria/python directory
## 'commands run zambia_calib'

import os
import sys
import json
import numpy as np

from simtools.SetupParser import SetupParser
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.vector.study_sites import configure_site
from dtk.interventions.outbreak import recurring_outbreak
from dtk.utils.reports.report_manager import add_reports

from dtk.interventions.itn import add_ITN_mult 
from dtk.interventions.health_seeking import add_health_seeking

from dtk.interventions.malaria_drugs import add_drug_campaign_multi_dosing, add_drug_campaign
from dtk.interventions.habitat_scale import scale_larval_habitats

import dtk.generic.demographics as demographics
from dtk.utils.parsers.json2dict import json2dict

campaign_days = [365*year + 160 for year in range(6,10)]
setup = SetupParser()
nyears = 12 # simulation duration; starting on  1/1/2005
dll_root = setup.get('BINARIES', 'dll_path')
location = 'HPC' # 'LOCAL'

geography = 'Zambia/Sinamalima_1_node' 
single_node = [1631855152]
site = 'Sinamalima_1_node'
demographics_filename = "sinamalima_30arcsec_demographics_alt_600.json"


nets_calib = json2dict('cluster_tags_net_usage_single_node_updated.json')

nets_campaigns = {
                  'campaigns':[]
                  }



drug_campaigns = {
                  'campaigns':[]
                  
                  }
#[0.35,0.55,0.7]
drug_coverages = [0.7]
exp_name  = site + '_MSAT_'+str(drug_coverages[0])+'_w_pilot_calib'
for coverage in drug_coverages:
    drug_campaigns['campaigns'].append([])
    
    # pilot MSAT round
    drug_campaigns['campaigns'][-1].append(
                                           {
                                             'drug_code':'MSAT_AL_veh',
                                             'start_days':[year*365 + 344 for year in range(5,6)],
                                             'coverage':coverage,
                                             'repetitions':1,
                                             'interval':60
                                             }
                                           )
    
    # MACEPA MSAT campaign
    drug_campaigns['campaigns'][-1].append(
                                           {
                                             'drug_code':'MSAT_AL_veh',
                                             'start_days':[365*year + 160 for year in range(6,8)],
                                             'coverage':coverage,
                                             'repetitions':3,
                                             'interval':60
                                             }
                                           )
    
    # MACEPA ongoing and future MDA campaigns
    drug_campaigns['campaigns'][-1].append(
                                           {
                                             'drug_code':'MDA_DP_veh',
                                             'start_days':[365*year + 360 for year in range(8,9)],
                                             'coverage':coverage,
                                             'repetitions':2,
                                             'interval':60
                                             }
                                           )
    drug_campaigns['campaigns'][-1].append(
                                           {
                                             'drug_code':'MDA_DP_veh',
                                             'start_days':[365*year + 200 for year in range(9,10)],
                                             'coverage':coverage,
                                             'repetitions':3,
                                             'interval':40
                                             }
                                           )


for coverage, campaign in nets_calib.iteritems():

    if coverage == 'lowest' :
    #if coverage != 'data':
        print "Net campaigns with coverage " + coverage
        nets_campaigns['campaigns'].append([])
        for i,eff_dist in enumerate(campaign['best_match']['eff_dists']):
            nets_campaigns['campaigns'][-1].append(
                                                   (
                                                    (30*(i+1)*campaign['best_match']['period'],coverage),\
                                                    [ 
                                                            {'min':0,'max':5,'coverage':eff_dist[0]}, \
                                                            {'min':5,'max':30,'coverage':eff_dist[0] - eff_dist[0]*0.3}, \
                                                            {'min':30,'max':100,'coverage': eff_dist[0]}
                                                    ]
                                                    )
                                                   )
        print "NUM campaigns: " +  str(len(nets_campaigns['campaigns'][-1]))


# full span constant habitat       
constant_habitats = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.2, 1.4, 1.5, 1.8, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.5, 4, 4.5, 5, 6, 7, 8, 9, 10, 12]

# Gwembe/Lukonde (low prevalence)
#constant_habitats = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.2, 1.4, 1.5, 1.8, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.5, 4]

# full span all habitats
x_temp_habs = [0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.12, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.4, 2.8, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0]

# Gwembe/Lukonde (low prevalence)
#x_temp_habs = [0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.12, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.4, 2.8, 3.0, 3.5, 4.0]


scales = []
for constant_habitat in constant_habitats:
    scales.append((single_node, constant_habitat))

x_temp_habs_str = []
for x_temp_hab in x_temp_habs:
    x_temp_habs_str.append(str(x_temp_hab))

builder   = GenericSweepBuilder.from_mix({'Run_Number': range(5),
                                           'events': {
                                                      'add_ITN_mult':nets_campaigns\
                                                      ,'scale_larval_habitats_single': {
                                                                                'scale':scales,\
                                                                                'target':["CONSTANT"],\
                                                                                'variation':[0]
                                                                                }\
                                                      ,'add_drug_multi_campaigns':drug_campaigns
                                                      },
                                           'x_Temporary_Larval_Habitat':x_temp_habs, 
                                           '_site_'    : [site]})


# Load default config for sim_type
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

# demographics
cb.update_params({'Demographics_Filename':demographics_filename})

# modify the config for the geography of interest
cb.update_params({
                'Geography': geography,
                'Num_Cores': 1,
                'Simulation_Duration' : nyears*365,
                'New_Diagnostic_Sensitivity': 0.025 # 40/uL
                })

# tweaks
cb.update_params({
                'Birth_Rate_Dependence': 'FIXED_BIRTH_RATE', # to match demographics file for constant population size (with exponential age distribution)
                'Infection_Updates_Per_Timestep': 8,
                'Enable_Nondisease_Mortality': 1
                })

'''
# DEBUG mode
cb.update_params({
                  "logLevel_IndividualMalaria": "DEBUG",
                  "logLevel_InfectionMalaria": "DEBUG",
                  "logLevel_MalariaAntibody": "DEBUG"
                  })
'''

cb.update_params({'Enable_Demographics_Reporting':0})


# immune overlays
const_habitats_immune_ref = [1, 4, 8, 12]
const_habitats_immune = []
for const_h in constant_habitats:
    hidx = np.argmin(np.absolute(np.subtract(const_habitats_immune_ref,const_h)))
    const_habitats_immune.append(str(const_habitats_immune_ref[hidx])+'.0') # add .0 to habitat value to match float point format of immune overlay file name  
print const_habitats_immune 

demographics.add_immune_init_all_const(cb, "Gwembe_1_node", x_temp_habs_str, const_habitats_immune)

# recurring outbreak to avoid fadeout
recurring_outbreak(cb, tsteps_btwn=180)

# baseline health-seeking
add_health_seeking(cb,5*365,
                    drug = ['Artemether','Lumefantrine'],
                    targets = [ { 'trigger': 'NewClinicalCase', 'coverage': 0.8, 'agemin':0, 'agemax':5, 'seek': 0.4, 'rate': 0},
                                { 'trigger': 'NewClinicalCase', 'coverage': 0.6, 'agemin':5, 'agemax':100, 'seek': 0.4, 'rate': 0 } ])

# Add drugs

'''
add_drug_campaign(cb, 'MSAT_AL', coverage=0.7, repetitions=3, interval=60, start_days=[365*year + 160 for year in range(4,6)])
add_drug_campaign(cb, 'MDA_DP', coverage=0.7, repetitions=2, interval=60, start_days=[365*year + 360 for year in range(6,7)])
add_drug_campaign(cb, 'MDA_DP', coverage=0.7, repetitions=3, interval=40, start_days=[365*year + 200 for year in range(7,8)])
'''

'''
add_drug_campaign_multi_dosing(cb, 'MSAT_AL_veh', coverage=0.7, repetitions=3, interval=60, start_days=[365*year + 160 for year in range(6,8)])
add_drug_campaign_multi_dosing(cb, 'MDA_DP_veh', coverage=0.7, repetitions=2, interval=60, start_days=[365*year + 360 for year in range(8,9)])
add_drug_campaign_multi_dosing(cb, 'MDA_DP_veh', coverage=0.7, repetitions=3, interval=40, start_days=[365*year + 200 for year in range(9,10)])
'''


reports = {
           'MalariaSummaryReportAnnual' : { 'Start Day' : 0, 'Reporting Interval' : 365, 'Report Description' : 'Annual', 'Max Number of Reports':nyears}
           }

reports['MalariaImmunityReport'] = { 'Start Day' : 0, 'Reporting Interval' : 365, 'Max Number of Reports':1, 'Report Description' : 'DebugImmunity', 'Age Bins': [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 40,  50,  60, 1000 ]}
                                           
campaign_days = [6*365 + 160, 6*365 + 160 + 60, 6*365 + 160 + 60 + 60, 7*365 + 160, 7*365 + 160 + 60, 7*365 + 160 + 60 + 60, 8*365 + 360, 8*365 + 360 + 60, 9*365 + 200, 9*365 + 200 + 40, 9*365 + 200 + 40 + 40]

for day in campaign_days:
    reports['MalariaSurveyJSONAnalyzer_5_days_Prior_' + str(day-5)] = {'Survey Start Days' : [day-5], 'Reporting Interval' : 365,  'Reporting Duration' : 1}
    reports['MalariaSurveyJSONAnalyzer_5_days_After_' + str(day+5)] = {'Survey Start Days' : [day+5], 'Reporting Interval' : 365, 'Reporting Duration' : 1}

    
dlls = add_reports(cb, dll_root, reports=reports)

# Return dictionary of keyword-arguments for DTKSimulationManager.RunSimulations
run_sim_args =  { 'config_builder': cb,
                    'exp_name': exp_name,
                    'exp_builder': builder}