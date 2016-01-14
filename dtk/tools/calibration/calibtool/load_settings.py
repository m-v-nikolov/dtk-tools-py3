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

def load_settings(ofname) :
    # the calibration defaults are in a JSON file in the same folder as this script
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'calibration_defaults.json')) as fin :
        settings = json.loads(fin.read())

    if ofname :
        try :
            with open(ofname) as fin :
                settings = overlay(settings, json.loads(fin.read()))
        except IOError :
            pass

    # Normalize the paths to allow the user to specify paths with / or \
    settings['working_dir'] = os.path.normpath(settings['working_dir'])
    settings['dtk_setup_config'] = os.path.normpath(settings['dtk_setup_config'])
    settings['initial_sampling_range_file'] = os.path.normpath(settings['initial_sampling_range_file'])
    settings['initial_sampling_range_file'] = os.path.normpath(settings['initial_sampling_range_file'])

    # Make sure the exp_dir exists
    settings['exp_dir'] = os.path.join( settings['working_dir'], settings['expname'])
    try :
        os.mkdir(settings['exp_dir'])
    except WindowsError :
        pass

    newrun = True
    try :
        with open(os.path.join(settings['exp_dir'],'settings.json')) as fin :
            settings = json.loads(fin.read())
            newrun = False
    except IOError :        
        settings['plot_dir'] = os.path.join(settings['exp_dir'],'_plots')
        settings['curr_iteration_dir'] = os.path.join(settings['exp_dir'],'iter0')
        with open(settings['dtk_setup_config']) as fin :
            if 'hpc' in settings['run_location'].lower() :
                loc = 'hpc'
            else :
                loc = 'local'

            cfg = fin.read()
            sec = filter(lambda x : loc.upper() in x, cfg.split('['))[0]
            simroot = filter(lambda x : 'sim_root' in x, sec.split('\n'))[0]
            settings['simulation_dir'] = simroot.split()[-1]
            settings[loc + '_sim_root'] = simroot.split()[-1]
            inputroot = filter(lambda x : 'input_root' in x, sec.split('\n'))[0]
            settings[loc + '_input_root'] = inputroot.split()[-1]

        with open(os.path.join(settings['exp_dir'],'settings.json'), 'w') as fout :
            json.dump(settings, fout, sort_keys=True, indent=4, separators=(',', ': '))

    try :
        os.mkdir(settings['working_dir'])
    except WindowsError :
        pass

    try :
        os.mkdir(settings['plot_dir'])
    except WindowsError :
        pass

    try :
        os.mkdir(settings['curr_iteration_dir'])
    except WindowsError :
        pass

    return settings

def overlay(base_settings, overlay_settings) :

    for key in overlay_settings :
        base_settings[key] = overlay_settings[key]
    return base_settings

def load_analyzers(settings) :

    try :
        with open(os.path.join(settings['exp_dir'],'analyzers.json')) as fin :
            analyzers = json.loads(fin.read())
    except IOError :
        analyzers = {}
        from study_sites.set_calibration_site import get_analyzers
        for site in settings['sites'] :
            for analyzer in settings['sites'][site] :
                analyzers[analyzer] = get_analyzers(site, analyzer)
        with open(os.path.join(settings['exp_dir'],'analyzers.json'), 'w') as fout :
            json.dump(analyzers, fout, sort_keys=True, indent=4, separators=(',', ': '))

    return analyzers


def load_all_settings(ofname) :

    settings = load_settings(ofname)
    analyzers = load_analyzers(settings)
    return settings, analyzers
    
