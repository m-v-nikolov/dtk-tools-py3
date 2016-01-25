import json
import os
import sys
from copy import deepcopy as dcopy
from shutil import copy as shcopy
from analyze import analyze
from load_settings import load_all_settings
from next_parameters import update_params
from tools.calibration.calibtool.load_parameters import load_samples
from utils import check_for_done, update_settings, concat_likelihoods
from visualize import visualize
from write_builder import write_submission


def run(ofname) :

    settings, analyzers = load_all_settings(ofname)
    print 'beginning calibration', settings['expname']
    samples = {}

    for iteration in range(settings['max_iterations']) :

        print 'updating for new iteration', iteration
        settings = update_settings(settings, iteration)

        print 'generating params for iteration', iteration
        keep_going = update_params(settings, iteration, samples, updater=settings['updater'])
        if not keep_going :
            break

        print 'running iteration', iteration
        run_one_iteration(settings, iteration)
        if settings['sim_type'] == 'MALARIA_SIM' :
            check_for_done(settings)

        print 'analyzing iteration', iteration
        samples = analyze(settings, analyzers, iteration)
        concat_likelihoods(settings)

        print 'visualizing iteration', iteration
        visualize(settings, iteration, analyzers, num_param_sets=settings['num_to_plot'])

def run_one_iteration(settings, iteration=0) :
    if os.path.exists(os.path.join(settings['curr_iteration_dir'],'sim.json')):
        return False

    # First load the samples
    samples = load_samples(settings, iteration)
    numvals = len(samples.index)


    # For each sites, configure the builder to change each of the parameters
    from dtk.utils.builders.sweep import Builder
    from dtk.tools.calibration.calibtool.study_sites.set_calibration_site import set_calibration_site
    from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
    from dtk.utils.core.DTKConfigBuilder import set_param
    from dtk.utils.simulation.SimulationManager import SimulationManagerFactory
    from dtk.utils.core.DTKSetupParser import DTKSetupParser

    builders = list()

    # For each param = value, create a simulation
    for i in range(numvals) :
        current_sim = list()
        for pname in samples.columns.values :
            pval = str(samples[pname].values[i])
            current_sim.append(Builder.ModFn(set_param,pname,pval))

        # For each sites and run_number, duplicate the simulation, add the site and add to the builder list
        for site in settings['sites']:
            for run_num in range(settings['sim_runs_per_param_set']) :
                current_sim_site = dcopy(current_sim)
                current_sim_site.append(Builder.ModFn(set_calibration_site,site))
                current_sim_site.append(Builder.ModFn(set_param,'Run_Number',run_num))
                builders.append(current_sim_site)


    # Create the configbuilder
    builder = Builder.from_list(builders)
    cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
    location = 'HPC' if ('hpc' in settings['run_location'].lower()) else 'LOCAL'
    setup = DTKSetupParser()
    sm = SimulationManagerFactory.from_exe(setup.get('BINARIES','exe_path'),location)
    # Run the simulation
    args = {
        'config_builder': cb,
        'exp_name': settings['expname'],
        'exp_builder': builder
    }
    sm.RunSimulations(**args)

    sim_json_dir = 'simulations\\'
    os.system('dir ' + sim_json_dir + ' /o:d > simIDs')
    fname = ""

    with open('simIDs') as fin :
        t = fin.readlines()
        for i in reversed(range(len(t))) :
            if 'json' in t[i] :
                fname = t[i].split()[-1]
                break

    with open(os.path.join(sim_json_dir,fname)) as fin :
        t = json.loads(fin.read())
        with open(os.path.join(settings['curr_iteration_dir'],'sim.json'), 'w') as fout :
            json.dump(t, fout)



def run_one_iteration1(settings, iteration=0) :

    if settings['sim_type'] == 'MALARIA_SIM' :
        try :
            with open(os.path.join(settings['curr_iteration_dir'],'sim.json')) as fin :
                return False
        except IOError :
            if os.path.isfile(os.path.join(settings['curr_iteration_dir'],'temp_dtk.py')) :
                shcopy(os.path.join(settings['curr_iteration_dir'], 'temp_dtk.py'), '.')
            else :
                print 'building dtk script'
                write_submission(settings, iteration)
                shcopy('temp_dtk.py', settings['curr_iteration_dir'])
            print 'submitting dtk script'
            os.system('dtk run temp_dtk ' + settings['run_location'])
            sim_json_dir = 'simulations\\'
            os.system('dir ' + sim_json_dir + ' /o:d > simIDs')
            fname = ""

            with open('simIDs') as fin :
                t = fin.readlines()
                for i in reversed(range(len(t))) :
                    if 'json' in t[i] :
                        fname = t[i].split()[-1]
                        break

            with open(os.path.join(sim_json_dir,fname)) as fin :
                t = json.loads(fin.read())
                with open(os.path.join(settings['curr_iteration_dir'],'sim.json'), 'w') as fout :
                    json.dump(t, fout)

if __name__ == '__main__':

    if len(sys.argv) > 1 :
        ofname = sys.argv[1]
        run(ofname)
    else :
        run('calibration_overlays.json')
    