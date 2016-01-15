from load_settings import load_all_settings
from write_builder import write_submission
from analyze import analyze
from visualize import visualize
import os
import sys
from utils import clean_directory, check_for_done, update_settings, concat_likelihoods
from next_parameters import update_params
import json
from shutil import copy as shcopy

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
            with open('simIDs') as fin :
                t = fin.readlines()
                for i in reversed(range(len(t))) :
                    if 'json' in t[i] :
                        fname = t[i].split()[-1]
                        break
            with open(sim_json_dir + fname) as fin :
                t = json.loads(fin.read())
                with open(os.path.join(settings['curr_iteration_dir'],'sim.json'), 'w') as fout :
                    json.dump(t, fout)

if __name__ == '__main__':

    if len(sys.argv) > 1 :
        ofname = sys.argv[1]
        run(ofname)
    else :
        run('calibration_overlays.json')
    