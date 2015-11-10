from load_parameters import load_samples
import pandas as pd

def write_submission(settings, iteration) :

    if 'hpc' in settings['run_location'].lower() :
        write_dtk_cfg(settings)
    samples = load_samples(settings, iteration)
    numvals = len(samples.index)

    modstr = ''
    for i in range(numvals) :
        parstr = ''
        for pname in samples.columns.values :
            pval = str(samples[pname].values[i])
            mystr = ''
            if 'CAMPAIGN' in pname :
                vname = pname.split('.')
                if vname[1] == 'DRUG' :
                    camp_code = vname[2]
                    start_day = vname[3]
                    mystr = 'Builder.ModFn(add_drug_campaign, \'' + camp_code + '\', start_days=[' + start_day + '], coverage=' + pval + ', repetitions=1),'
            elif 'HABSCALE' in pname :
                node = pname.split('.')[1]
                mystr = 'Builder.ModFn(scale_larval_habitats, [([\'' + node + '\'], \'' + pval + '\')]),'
            elif 'VECTOR' in pname :
                vname = pname.split('.')[1]
                vpar = pname.split('.')[2]
                set_param = True
                if 'Required_Habitat_Factor' in vpar :
                    if vname + '.Required_Habitat_Factor' not in parstr :
                        habnames = [x for x in samples.columns.values if vname+'.Required_Habitat_Factor' in x]
                        habvals = [samples[x].values[i] for x in habnames]
                        mystr = 'Builder.ModFn(set_larval_habitat, {\'' + vname + '\':{' + ','.join(['\'' + habnames[x].split('.')[3] + '\':' + str(habvals[x]) for x in range(len(habnames))]) + '}}),'
                else :
                    mystr = 'Builder.ModFn(set_species_param, \'' + vname + '\', \'' + vpar + '\', value=' + pval + '),'
                pval = str(samples[pname].values[i])
            elif 'DRUG' in pname :
                vname = pname.split('.')[1]
                vpar = pname.split('.')[2]
                mystr = 'Builder.ModFn(set_drug_param, \'' + vname + '\', \'' + vpar + '\', value=' + pval + '),'
            
            mystr += 'Builder.ModFn(set_param, \'' + pname + '\', ' + pval + '),'
            parstr += mystr
        for site in settings['sites'] :
            for run_num in range(settings['sim_runs_per_param_set']) :
                modstr = modstr+'[Builder.ModFn(set_calibration_site, \'' + site + '\'),' + parstr + 'Builder.ModFn(set_param, \'Run_Number\', ' + str(run_num) + ')],'
    modstr = modstr[:-1]

    with open('temp_dtk.py', 'w') as fout :
        fout.write("""
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder, set_param
from dtk.utils.builders.sweep import Builder
from dtk.vector.species import set_larval_habitat, set_species_param
from dtk.interventions.malaria_drugs import set_drug_param, add_drug_campaign
from dtk.interventions.habitat_scale import scale_larval_habitats
from dtk.tools.calibration.calibtool.study_sites.set_calibration_site import set_calibration_site

exp_name  = \'""" + settings['expname'] + """\'

# Load default config for sim_type
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

builder = Builder.from_list([""" + modstr + """])

run_sim_args =  {   'config_builder': cb,
                    'exp_name': exp_name,
                    'exp_builder': builder}

""")

def write_dtk_cfg(settings) :

    with open(settings['dtk_setup_config']) as fin :
        cfg = [x[:-1] for x in fin.readlines()]
        for i, line in enumerate(cfg) :
            if 'priority' in line :
                p = line.split()
                p[-1] = settings['hpc_priority']
                break
        cfg[i] = ' '.join(p)
    with open(settings['dtk_setup_config'], 'w') as fout :
        fout.write('\n'.join(cfg))