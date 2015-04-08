#####################################################################
# utils.py
#
# Helpful utility functions
#
# write_to_file()
#
# update_settings()
#
# clean_directory()
#
# check_for_done()
#
#####################################################################


import json
import os
import time

def write_to_file(samples, outstem, types=['json', 'txt']) :

    for fout_type in types :
        if fout_type == 'json' :
            with open(outstem + '.json', 'w') as fout :
                json.dump(samples, fout)
        else :
            with open(outstem + '.' + fout_type, 'w') as fout :
                my_keys = samples.keys()
                numsamples = len(samples[samples.keys()[0]])
                fout.write('\t'.join(my_keys) + '\n')
                for i in range(numsamples) :
                    fout.write('\t'.join([str(samples[x][i]) for x in my_keys]) + '\n')

def update_settings(settings, iteration) :

    settings['curr_iteration_dir'] = settings['exp_dir'] + 'iter' + str(iteration) + '/'
    settings['prev_iteration_dir'] = settings['exp_dir'] + 'iter' + str(iteration-1) + '/'
    try :
        os.mkdir(settings['curr_iteration_dir'])
    except WindowsError :
        pass

    return settings

def clean_directory(settings) :

    this_dir = settings['curr_iteration_dir']
    sites = settings['sites'].keys()

    try :
        os.remove(this_dir + 'params.json')
        os.remove(this_dir + 'exp')
        os.remove(this_dir + 'params_withpaths.json')
        os.remove(this_dir + 'params_withpaths.txt')
        for site in sites :
            os.remove(this_dir + 'parsed_' + site + '.json')
        os.remove(this_dir + 'LL.json')
        os.remove(this_dir + 'LL.txt')

    except WindowsError :
        pass
    
def check_for_done(sleeptime=0) :

    if sleeptime > 0 :
        time.sleep(sleeptime)
        return

    status_fname = 'temp'
    numsims = -1

    start_time = time.time()
    start_run_time = -1

    while True :
        os.system('dtk status > ' + status_fname)
        status = reset_status()
        with open(status_fname) as fin :
            f = fin.read()
            t = f.split('{')[-1].split('}')[0]
            if numsims < 0 :
                numsims = len(f.split('{')[-2].split('}')[0].split(','))
            for line in t.split(',') :
                status[line.split()[0][1:-2]] = int(line.split()[1])
        if status['Succeeded'] + status['Failed'] + status['Canceled'] + status['Finished'] == numsims :
            break
        curr_time = time.time() - start_time
        status['Finished'] = status['Succeeded'] + status['Failed'] + status['Canceled'] + status['Finished']
        status['Waiting'] = status['Commissioned'] + status['CommissionRequested'] + status['Provisioning']
        if start_run_time < 0 and status['Finished'] + status['Running'] > 0 :
            start_run_time = curr_time

        print 'time since submission: ', int(curr_time/60), 
        print 'time_since running began: ', int((curr_time - start_run_time)/60)
        print 'Running: ' + str(status['Running']), 
        print 'Waiting: ' + str(status['Waiting']), 
        print 'Finished: ' + str(status['Finished'])
        time.sleep(get_sleep_time(status, numsims, curr_time, start_run_time))


def reset_status() :

    status = { 'Commissioned' : 0, 'Running' : 0, 'Succeeded' : 0, 'Failed' : 0, 
               'Canceled' : 0, 'Created' : 0, 'CommissionRequested' : 0, 
               'Provisioning' : 0, 'Retry' : 0, 'CancelRequested' : 0, 
               'Finished' : 0, 'Waiting' : 0}

    return status

def get_sleep_time(status, numsims, curr_time, start_run_time) :

    if status['Waiting'] == numsims :
        return min([max([60, curr_time*2]), 300])
    if status['Running'] < 0.5*numsims :
        return min([max([60, start_run_time*2]), 300])
    if (status['Finished']) > 0 :
        return min([60, 10*status['Running']])

    return 60
