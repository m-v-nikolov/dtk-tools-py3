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
# cleanup()
#####################################################################


import json
import os
import time
import pandas as pd
import math

def concat_likelihoods(settings) :

    df = pd.DataFrame()
    for i in range(settings['max_iterations']) :
        try :
            LL = pd.read_csv(settings['exp_dir'] + 'iter' + str(i) + '/LL.csv')
            LL['iteration'] = pd.Series([i]*len(LL.index))
            df = pd.concat([df, LL])
        except IOError :
            break
    write_to_file(df, settings['exp_dir'] + 'LL_all')

def write_to_file(samples, outstem) :

    samples.to_csv(outstem + '.csv', index=False)

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
    
def check_for_done(settings, sleeptime=0) :

    with open(settings['curr_iteration_dir'] + 'sim.json') as fin :
        sim = json.loads(fin.read())
    exp_id = sim['exp_name'] + '_' + sim['exp_id']

    if sleeptime > 0 :
        time.sleep(sleeptime)
        return

    status_fname = 'temp'
    numsims = -1

    start_time = time.time()
    start_run_time = -1

    while True :
        os.system('dtk status -e ' + exp_id + ' > ' + status_fname)
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

def calc_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    km = 6371 * c
    return km

def latlon_to_anon(lats, lons, reflat=0, reflon=0) :

    if reflat == 0 or reflon == 0 :
        reflat = lats[0]
        reflon = lons[0]

    ycoord = [calc_distance(x, reflon, reflat, reflon) for x in lats]
    xcoord = [calc_distance(reflat, x, reflat, reflon) for x in lons]
    for i in range(len(lats)) :
        if lats[i] < reflat :
            ycoord[i] *= -1
        if lons[i] < reflon :
            xcoord[i] *= -1
    midx = (max(xcoord) + min(xcoord))/2
    midy = (max(ycoord) + min(ycoord))/2
    xcoord = [x - midx for x in xcoord]
    ycoord = [x - midy for x in ycoord]

    return xcoord, ycoord