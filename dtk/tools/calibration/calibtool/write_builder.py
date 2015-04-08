from load_parameters import load_samples

def write_submission(settings, iteration) :

    if iteration == 0 :
        write_dtk_setup(settings)
    pnames, pvals = get_parameters(settings, iteration)
    sitestring = '[' + ', '.join(['\'' + x + '\'' for x in settings['sites'].keys()]) + ']'

    with open('temp_dtk.py', 'w') as fout :
        fout.write("""

import os
from dtk.utils.core.DTKSetupParser import DTKSetupParser
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.generic.demographics import add_immune_overlays, set_immune_mod
from sweep_calibration import GenericSweepBuilder

setup = DTKSetupParser()
dll_root = setup.get('BINARIES', 'dll_path')

exp_name  = \'""" + settings['expname'] + """\'

sites = """ + sitestring + """
params_to_test = """ + pnames + """
param_vals = """ + pvals + """

num_params = len(params_to_test)
num_vals = len(param_vals[0])

simlist = []
for site in sites :
    for j in range(num_vals) :
        t = (site, )
        for i in range(num_params) :
            t = t + (param_vals[i][j],)
        simlist.append(t)

# Load default config for sim_type
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')

builder = GenericSweepBuilder.from_list(['_site_']+params_to_test,
                                        simlist, """ + str(settings['geographies']) + """)

dlls = [os.path.join(dll_root, 'libmalariasummary_report_plugin.dll'), os.path.join(dll_root, 'libmalariasurveyJSON_analyzer_plugin.dll')]

run_sim_args =  {   'config_builder': cb,
                    'exp_name': exp_name,
                    'exp_builder': builder}

if __name__ == "__main__":

    from dtk.utils.core.DTKSetupParser import DTKSetupParser
    from dtk.utils.simulation.SimulationManager import SimulationManagerFactory

    sm = SimulationManagerFactory.from_exe(DTKSetupParser().get('BINARIES','exe_path'),'LOCAL')
    sm.RunSimulations(**run_sim_args)

    """)


def get_parameters(settings, iteration) :

    samples = load_samples(settings, iteration)

    pnames = samples.keys()
    pvals = []
    for p in pnames :
        pvals.append(', '.join([str(x) for x in samples[p]]))

    return '[' + ', '.join(['\'' + x + '\'' for x in pnames]) + ']', '[[' + '], ['.join(pvals) + ']]'

def write_dtk_setup(settings) :

    with open(settings['dtk_setup_config'], 'w') as fout :
        fout.write("""
[HPC]
server_endpoint = """ + settings['hpc_server_endpoint'] + """
node_group      = """ + settings['hpc_node_group'] + """
priority        = """ + settings['hpc_priority'] + """
sim_root        = """ + settings['hpc_sim_root'] + settings['expname'] + """\\ 
input_root      = """ + settings['hpc_input_root'] + """
bin_root        = """ + settings['hpc_bin_root'] + """
dll_root        = """ + settings['hpc_dll_root'] + """
num_retries     = """ + settings['hpc_num_retries'] + """
sims_per_thread = """ + settings['hpc_sims_per_thread'] + """
max_threads     = """ + settings['hpc_max_threads'] + """

[HPC-OLD]
username   = NA\jgerardin
#password   = [password] # not necessary if credentials are cached locally
head_node  = idmpphpc01
node_group = emod_abcd
priority   = Lowest
sim_root   = \\\\idmppfil01\\IDM\home\\%(user)s\\output\\simulations\\
input_root = \\\\idmppfil01\\IDM\home\\%(user)s\\input\\
bin_root   = \\\\idmppfil01\\IDM\home\\%(user)s\\bin\\
dll_root   = \\\\idmppfil01\\IDM\home\\%(user)s\\emodules\\

[LOCAL]
sim_root   = """ + settings['local_sim_root'] + """
input_root = """ + settings['local_input_root'] + """
bin_root   = """ + settings['local_bin_root'] + """
dll_root   = """ + settings['local_dll_root'] + """
max_local_sims = 3

[BINARIES]
exe_path   = """ + settings['binaries_exe_path'] + """
dll_path   = """ + settings['binaries_dll_path'] + """

    """)
