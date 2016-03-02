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

from dtk.utils.core.DTKSetupParser import DTKSetupParser

def load_settings(ofname) :
    # the calibration defaults are in a JSON file in the same folder as this script
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'calibration_defaults.json')) as fin :
        settings = json.loads(fin.read())

    if ofname :
        try :
            with open(ofname) as fin :
                settings = overlay(settings, json.loads(fin.read()))
        except IOError :
            #pass
            raise Exception('Failed to open overlay file %s' % ofname)


    # Normalize the paths to allow the user to specify paths with / or \
    settings['working_dir'] = os.path.normpath(settings['working_dir'])
    settings['initial_sampling_range_file'] = os.path.normpath(settings['initial_sampling_range_file'])

    # Add the custom sites to the path
    sys.path.insert(0,os.path.join(settings['working_dir'], settings['custom_sites_module']))

    # Make sure the exp_dir exists
    settings['exp_dir'] = os.path.join( settings['working_dir'], settings['expname'])
    try :
        os.mkdir(settings['exp_dir'])
    except OSError :
        pass

    try :
        with open(os.path.join(settings['exp_dir'],'settings.json')) as fin :
            settings = json.loads(fin.read())
    except IOError :
        settings['plot_dir'] = os.path.join(settings['exp_dir'],'_plots')
        settings['curr_iteration_dir'] = os.path.join(settings['exp_dir'],'iter0')
        
        loc = 'HPC' if 'HPC' in settings['run_location'].upper() else 'LOCAL'
        cfg = DTKSetupParser()
        settings['simulation_dir'] = cfg.get(loc, 'sim_root')
        settings[loc.lower() + '_sim_root'] = cfg.get(loc, 'sim_root')
        settings[loc.lower() + '_input_root'] = cfg.get(loc, 'input_root')

        with open(os.path.join(settings['exp_dir'],'settings.json'), 'w') as fout :
            json.dump(settings, fout, sort_keys=True, indent=4, separators=(',', ': '))

    try :
        os.mkdir(settings['working_dir'])
    except OSError :
        pass

    try :
        os.mkdir(settings['plot_dir'])
    except OSError :
        pass

    try :
        os.mkdir(settings['curr_iteration_dir'])
    except OSError :
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
