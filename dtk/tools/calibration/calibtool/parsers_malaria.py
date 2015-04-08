#####################################################################
# parsers.py
#
# A set of functions that grabs DTK output of interest for each site
# and analyzer, saving output paths and parsed data by site to current
# working directory.
#
# get_site_data()
# ---
# args : calibration settings, analyzer settings, site, iteration
# return : dictionary of output data by site. Format of each element
# of data dictionary is analyzer-dependent.
# If site data is already parsed, load directly from parsed data json
# file. Else load the output paths and get data according to reporter
# type listed in analyzer settings.
# 
# get_site_data() is called from analyzer.py
#
#####################################################################

import os
import json
from load_parameters import load_samples
from utils import write_to_file

def get_site_data(settings, analyzers, site, iteration) :

    parsed_file = settings['curr_iteration_dir'] + 'parsed_' + site + '.json'

    try :
        with open(parsed_file) as fin :
            data = json.loads(fin.read())

    except IOError :
        samples = load_output_paths(settings, iteration)
        numsamples = len(samples[site + ' outpath'])

        data = {}
        for this_analyzer in settings['sites'][site] :
            if 'Summary Report' in analyzers[this_analyzer]['reporter'] :
                data[this_analyzer] = get_summary_report_data(analyzers[this_analyzer], samples[site + ' outpath'])
            elif 'Survey Report' in analyzers[this_analyzer]['reporter'] :
                data[this_analyzer] = get_survey_report_data(analyzers[this_analyzer], samples[site + ' outpath'])

        with open(parsed_file, 'w') as fout :
            json.dump(data, fout)

    return data

def load_output_paths(settings, iteration) :

    parfile = settings['curr_iteration_dir'] + 'params' + '.json'
    pathfile = settings['curr_iteration_dir'] + 'params' + '_withpaths'
    try :
        with open(pathfile + '.json') as fin :
            samples = json.loads(fin.read())

    except IOError :
        if 'hpc' in settings['run_location'].lower() :
            samples = get_paths_hpc(settings, iteration)
        else :
            samples = get_paths_local(settings, iteration)
        write_to_file(samples, pathfile, types=['json', 'txt'])

    return samples

def get_survey_report_data(analyzer, simpaths) :

    numsamples = len(simpaths)
    simfile = 'MalariaSurveyJSONAnalyzer_Day_' + str(analyzer['start_day']) + '_' + str(0) + '.json'
    data = []
    for i in range(numsamples) :
        t = loaddata(simpaths[i] + '/output/' + simfile)
        patients = []
        for patient in t['patient_array'] :
            d = {}
            for f in analyzer['fields_to_get'] :
                if f == 'initial_age' :
                    d[f] = patient[f]
                else :
                    d[f] = patient[f][0]
            patients.append(d)
        data.append(patients)
    return data

def get_summary_report_data(analyzer, simpaths) :

    numsamples = len(simpaths)

    data = {}
    simfile = 'MalariaSummaryReport_' + analyzer['reporter'].split()[0] + '_Report.json'
    for field in analyzer['fields_to_get'] :
        data[field] = []
    for i in range(numsamples) :
        summary_data = loaddata(simpaths[i] + '/output/' + simfile)
        for field in analyzer['fields_to_get'] :
            data[field].append(summary_data[field])
    return data
        
def loaddata(fname) :

    with open(fname) as fin :
        data = json.loads(fin.read())
        return data

def get_paths_hpc(settings, iteration) :

    sites = settings['sites'].keys()

    samples = load_samples(settings, iteration)
    paramnames = samples.keys()
    numsamples = len(samples[paramnames[0]])
    
    sim_map = createSimDirectoryMap(settings)

    unmatched_params = {}
    for site in sites :
        samples[site + ' outpath'] = [0]*numsamples

    for sim_key in sim_map :
        site = sim_map[sim_key]['_site_']
        for p in range(numsamples) :
            match = True
            for pname in paramnames :
                if abs(float(sim_map[sim_key][pname]) - samples[pname][p]) > settings['ERROR'] :
                    match = False
                    break
            if match :
                samples[site + ' outpath'][p] = sim_map[sim_key]['output_path']
                break

    return samples


def get_paths_local(settings, iteration) :

    sites = settings['sites'].keys()

    samples = load_samples(settings, iteration)
    paramnames = samples.keys()
    numsamples = len(samples[paramnames[0]])
    
    subdirs = get_directories_local(settings['simulation_dir'], settings['expname'])
    unmatched_params = {}
    for site in sites :
        samples[site + ' outpath'] = [0]*numsamples
        unmatched_params[site] = range(numsamples)

    for sindex in range(len(subdirs)) :
        with open(subdirs[sindex] + '/config.json') as fin :
            config_params = json.loads(fin.read())['parameters']
            site = config_params['_site_']
            for p in unmatched_params[site] :
                match = True
                for pname in paramnames :
                    if abs(config_params[pname] - samples[pname][p]) > settings['ERROR'] :
                        match = False
                        break
                if match :
                    samples[site + ' outpath'][p] = subdirs[sindex]
                    unmatched_params[site].remove(p)
                    break

    return samples

def get_directories_local(sim_dir, expname) :

    lsout = filter(lambda(x) : expname in x, os.listdir(sim_dir))
    mydir = sorted(lsout)[-1]
    subdirs = sorted(os.listdir(sim_dir + mydir))

    subdirpaths = []
    for subdir in subdirs :
        subdirpaths.append(sim_dir + mydir + '/' + subdir)

    return subdirpaths
    
def createSimDirectoryMap(settings):

    with open(settings['curr_iteration_dir'] + 'simIDs') as fin :
        t = fin.readlines()
        for i in reversed(range(len(t))) :
            if 'json' in t[i] :
                fname = t[i].split()[-1]
                break
    with open(settings['calibtool_dir'] + 'simulations/' + fname) as fin :
        for line in fin.readlines() :
            if 'exp_id' in line :
                exp_id = line.split('\"')[3]
                break

    sim_json_dir = settings['calibtool_dir'] + 'simulations/'
    lsout = filter(lambda(x) : exp_id in x, os.listdir(sim_json_dir))

    fname = sorted(lsout)[-1]
    with open(sim_json_dir + fname) as fin :
        t = json.loads(fin.read())
        exp_id = t['exp_id']
        sim_keys = t['sims'].keys()
        sim_pars = t['sims']

    import sys
    sys.path.append(settings['dtk_path'])

    from COMPSJavaInterop import Experiment, QueryCriteria, Client
    Client.Login(settings['hpc_server_endpoint'])

    e = Experiment.GetById(exp_id)
    sims = e.GetSimulations(QueryCriteria().Select('Id').SelectChildren('HPCJobs')).toArray()
    sim_map = { sim.getId().toString() : sim.getHPCJobs().toArray()[-1].getWorkingDirectory() for sim in sims }
    for sim_id in sim_map :
        sim_pars[sim_id]['output_path'] = sim_map[sim_id]
    return sim_pars
