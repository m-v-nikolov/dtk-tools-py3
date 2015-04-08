########################################################################
# set calibration settings here! 
#
# - Experiment settings : experiment name, sites. See
# geography_calibration.py for setting site-specific configs and
# campaigns
#
# - CalibTool settings :
# number of samples, iterations, etc
# analyzers: which reporter fields are of interest
# which analyzers should be run for each site
#
# - HPC and local simulation settings, including exe and reporter dll
# paths
#
########################################################################
import os
import sys
import json

def load_settings() :

    settings = {}

    settings['expname'] = '150407_test1'
    settings['sites'] = { 'Malariatherapy' : ['malariatherapy_density_analyzer', 'malariatherapy_duration_analyzer']
                      }
                         
    # calibration sampling
    settings['num_initial_samples'] = 20
    settings['num_samples_per_iteration'] = 10
    settings['num_resamples'] = 10
    settings['max_iterations'] = 2
    settings['initial_sampling_type'] = 'LHC'

    settings['hpc_priority'] = 'Normal'

    settings['sim_type'] = 'MALARIA_SIM'
    #settings['weight_by_site'] = {}

    # paths
    settings['initial_sampling_range_file'] = 'C:/Users/jgerardin/work/calibtool/initial_sampling_range.json'
    settings['geography_file'] = 'C:/Users/jgerardin/work/calibtool/geographies_9sites.json'
    settings['calibtool_dir'] = 'C:/Users/jgerardin/SVN/python_github/dtk/dtk/tools/calibration/calibtool/'
    settings['working_dir'] = 'C:/Users/jgerardin/work/calibtool/'
    settings['exp_dir'] = settings['working_dir'] + settings['expname'] + '/'
    settings['curr_iteration_dir'] = settings['exp_dir'] + 'iter0/'
    settings['dtk_path'] = 'C:/Users/jgerardin/SVN/python_github/dtk/'
    settings['dtk_setup_config'] = settings['dtk_path'] + 'dtk_setup.cfg'

    settings['run_location'] = '--hpc' # '' for local, '--hpc' for HPC

    settings['ERROR'] = 10**-7

    # hpc settings
    settings['hpc_server_endpoint'] = 'https://comps.idmod.org'
    settings['hpc_node_group'] = 'emod_32cores'
    settings['hpc_sim_root'] = '\\\\idmppfil01\\IDM\home\\jgerardin\\output\\simulations\\'
    settings['hpc_input_root'] = '\\\\idmppfil01\\IDM\home\\jgerardin\\input\\'
    settings['hpc_bin_root'] = '\\\\idmppfil01\\IDM\home\\jgerardin\\bin\\'
    settings['hpc_dll_root'] = '\\\\idmppfil01\\IDM\home\\jgerardin\\emodules\\'
    settings['hpc_num_retries'] = '1'
    settings['hpc_sims_per_thread'] = '20'
    settings['hpc_max_threads'] = '50'
    # local simulation settings
    settings['local_sim_root'] = 'C:\\Users\\jgerardin\\SVN\\python\\simulations\\'
    settings['local_input_root'] = 'C:\\Users\\jgerardin\\Data_Files\\'
    settings['local_bin_root'] = 'C:\\Users\\jgerardin\\SVN\\python\\bin\\'
    settings['local_dll_root'] = 'C:\\Users\\jgerardin\\SVN\\python\\emodules\\'
    # exe and dll paths
    settings['binaries_exe_path'] = 'C:\\Users\\%(user)s\\Eradication\\Eradication\\x64\\Release\\Eradication.exe'
    settings['binaries_dll_path'] = 'C:\\Users\\%(user)s\\Eradication\\x64\\Release\\reporter_plugins\\'

    if 'hpc' in settings['run_location'].lower() :
        settings['simulation_dir'] = settings['hpc_sim_root']
    else :
        settings['simulation_dir'] = settings['local_sim_root']

    try :
        os.mkdir(settings['working_dir'])
    except WindowsError :
        pass

    try :
        os.mkdir(settings['exp_dir'])
    except WindowsError :
        pass

    try :
        os.mkdir(settings['curr_iteration_dir'])
    except WindowsError :
        pass

    try :
        with open(settings['exp_dir'] + 'settings.json') as fin :
            settings = json.loads(fin.read())
    except IOError :
        with open(settings['exp_dir'] + 'settings.json', 'w') as fout :
            json.dump(settings, fout, sort_keys=True, indent=4, separators=(',', ': '))

    with open(settings['geography_file']) as fin :
        settings['geographies'] = json.loads(fin.read())

    return settings

def load_analyzers(settings) :

    sys.path.append(settings['dtk_path'])
    from dtk.tools.calibration.calibtool.geography_calibration import get_geography_settings
    analyzers = {}
    analyzers['monthly_density_analyzer'] = { 'name' : 'monthly_density_analyzer',
                                              'reporter' : 'Monthly Summary Report',
                                              'fields_to_get' : ['PfPR by Parasitemia and Age Bin',
                                                                 'PfPR by Gametocytemia and Age Bin',
                                                                 'Average Population by Age Bin']
                                          }
    analyzers['seasonal_monthly_density_analyzer'] = analyzers['monthly_density_analyzer']
    analyzers['seasonal_monthly_density_analyzer']['name'] = 'seasonal_monthly_density_analyzer'
    analyzers['seasonal_monthly_density_analyzer']['seasons'] = { 'start_wet' : 6, 'peak_wet' : 8, 'end_wet' : 0}

    if 'Dapelogo' in settings['sites'] :
        i_rep = get_geography_settings('Dapelogo', settings['geographies'], 'report')
        analyzers['seasonal_infectiousness_analyzer'] = { 'name' : 'seasonal_infectiousness_analyzer',
                                                          'seasons' : { 'start_wet' : 6, 'peak_wet' : 8, 'end_wet' : 0},
                                                          'reporter' : 'Survey Report',
                                                          'start_day' : i_rep['MalariaSurveyJSONAnalyzer']['Survey Start Days'][0],
                                                          'interval' : i_rep['MalariaSurveyJSONAnalyzer']['Reporting Duration'],
                                                          'fields_to_get' : ['infectiousness', 'initial_age']
                                                      }

    analyzers['prevalence_by_age_analyzer'] = { 'name' : 'prevalence_by_age_analyzer',
                                                'reporter' : 'Annual Summary Report',
                                                'fields_to_get' : ['PfPR by Age Bin',
                                                                   'Average Population by Age Bin']
                                          }
    analyzers['annual_clinical_incidence_by_age_analyzer'] = { 'name' : 'annual_clinical_incidence_by_age_analyzer',
                                                               'reporter' : 'Annual Summary Report',
                                                               'fields_to_get' : ['Annual Clinical Incidence by Age Bin',
                                                                                  'Average Population by Age Bin',
                                                                                  'Age Bins']
                                                           }

    if 'Malariatherapy' in settings['sites'] :
        m_rep = get_geography_settings('Malariatherapy', settings['geographies'], 'report')
        analyzers['malariatherapy_density_analyzer'] = { 'name' : 'malariatherapy_density_analyzer',
                                                         'reporter' : 'Survey Report',
                                                         'start_day' : m_rep['MalariaSurveyJSONAnalyzer']['Survey Start Days'][0],
                                                         'interval' : m_rep['MalariaSurveyJSONAnalyzer']['Reporting Duration'],
                                                         'fields_to_get' : ['true_asexual_parasites', 'true_gametocytes']
                                                     }
        analyzers['malariatherapy_duration_analyzer'] = analyzers['malariatherapy_density_analyzer']
        analyzers['malariatherapy_duration_analyzer']['name'] = 'malariatherapy_duration_analyzer'


    try :
        with open(settings['exp_dir'] + 'analyzers.json') as fin :
            analyzers = json.loads(fin.read())
    except IOError :
        with open(settings['exp_dir'] + 'analyzers.json', 'w') as fout :
            json.dump(analyzers, fout, sort_keys=True, indent=4, separators=(',', ': '))

    return analyzers


def load_all_settings() :

    settings = load_settings()
    analyzers = load_analyzers(settings)
    return settings, analyzers
    
