from load_settings import load_all_settings
from write_builder import write_submission
from analyzers import analyze
from visualizer import visualize
import os
from utils import clean_directory, check_for_done, update_settings
from next_parameters import update_params

def run_one_iteration(settings, iteration=0) :

    if settings['sim_type'] == 'MALARIA_SIM' :
        try :
            with open(settings['curr_iteration_dir'] + 'exp') as fin :
                return False
        except IOError :
            write_submission(settings, iteration)
            os.system('dtk run temp_dtk ' + settings['run_location'] + ' > ' + settings['curr_iteration_dir'] + 'exp')
            os.system('dir simulations\\ /o:d > ' + settings['curr_iteration_dir'] + 'simIDs')
        return True
    return False

def run() :

    settings, analyzers = load_all_settings()
    samples = {}

    for iteration in range(settings['max_iterations']) :

        print 'updating for new iteration', iteration
        settings = update_settings(settings, iteration)

        print 'generating params for iteration', iteration
        keep_going = update_params(settings, iteration, samples, updater='IMIS')
        if not keep_going :
            break

        print 'running iteration ', iteration
        if run_one_iteration(settings, iteration) :
            if settings['sim_type'] == 'MALARIA_SIM' :
                check_for_done()

        print 'analyzing iteration ', iteration
        samples = analyze(settings, analyzers, iteration)

        visualize(settings, iteration, analyzers, num_param_sets=1)

if __name__ == '__main__':

    run()
