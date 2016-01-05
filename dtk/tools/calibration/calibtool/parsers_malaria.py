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
import pandas as pd
import struct
import numpy as np

def get_site_data(settings, analyzers, site, iteration) :

    parsed_file = settings['curr_iteration_dir'] + 'parsed_' + site + '.json'

    try :
        with open(parsed_file) as fin :
            data = json.loads(fin.read())

    except IOError :
        samples = load_output_paths(settings, iteration)

        data = {}
        for this_analyzer in settings['sites'][site] :
            data[this_analyzer] = []
            for run_num in range(settings['sim_runs_per_param_set']) :
                if 'Summary Report' in analyzers[this_analyzer]['reporter'] :
                    data[this_analyzer].append(get_summary_report_data(analyzers[this_analyzer], samples[site + ' outpath ' + str(run_num)].values))
                elif 'Survey Report' in analyzers[this_analyzer]['reporter'] :
                    data[this_analyzer].append(get_survey_report_data(analyzers[this_analyzer], samples[site + ' outpath ' + str(run_num)].values))
                elif 'Inset Chart' in analyzers[this_analyzer]['reporter'] :
                    data[this_analyzer].append(get_inset_chart_data(analyzers[this_analyzer], samples[site + ' outpath ' + str(run_num)].values))
                elif 'Spatial Report' in analyzers[this_analyzer]['reporter'] :
                    data[this_analyzer].append(get_spatial_report_data(analyzers[this_analyzer], samples[site + ' outpath ' + str(run_num)].values))

        with open(parsed_file, 'w') as fout :
            json.dump(data, fout)

    return data

def load_output_paths(settings, iteration) :

    parfile = settings['curr_iteration_dir'] + 'params' + '.csv'
    pathfile = settings['curr_iteration_dir'] + 'params' + '_withpaths'
    try :
        samples = pd.read_csv(pathfile + '.csv')

    except IOError :
        if 'hpc' in settings['run_location'].lower() :
            samples = get_paths_hpc(settings, iteration)
        else :
            samples = get_paths_local(settings, iteration)
        write_to_file(samples, pathfile)

    return samples

def get_survey_report_data(analyzer, simpaths) :

    numsamples = len(simpaths)
    simfile = 'MalariaSurveyJSONAnalyzer_Day_' + analyzer['reporter_output_tail'] + '.json'
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

def get_inset_chart_data(analyzer, simpaths) :

    numsamples = len(simpaths)

    data = {}
    simfile = 'InsetChart.json'
    for field in analyzer['fields_to_get'] :
        data[field] = []
    for i in range(numsamples) :
        inset_data = loaddata(simpaths[i] + '/output/' + simfile)
        for field in analyzer['fields_to_get'] :
            data[field].append(inset_data['Channels'][field]['Data'])
    return data

def get_spatial_report_data(analyzer, simpaths) :

    numsamples = len(simpaths)
    try :
        starttime = analyzer['burn_in']*365
    except KeyError :
        starttime = 0

    data = {}
    for field in analyzer['fields_to_get'] :
        data[field] = []
        simfile = 'SpatialReport_' + field + '.bin'
        for i in range(numsamples) :
            spatial_data = load_bin_file(simpaths[i] + '/output/' + simfile)

            data['nodeids'] = spatial_data['nodeids'].tolist()
            channeldata = spatial_data['data'][starttime:].tolist()
            if 'testdays' in analyzer :
                data[field].append([channeldata[x] for x in analyzer['testdays']])
            else :
                data[field].append(channeldata)

    return data

def load_bin_file(fname) :

    with open(fname, 'rb') as bin_file:
        data = bin_file.read(8)
        n_nodes, = struct.unpack( 'i', data[0:4] )
        n_tstep, = struct.unpack( 'i', data[4:8] )
        #print( "There are %d nodes and %d time steps" % (n_nodes, n_tstep) )

        nodeids_dtype = np.dtype( [ ( 'ids', '<i4', (1, n_nodes ) ) ] )
        nodeids = np.fromfile( bin_file, dtype=nodeids_dtype, count=1 )
        nodeids = nodeids['ids'][:,:,:].ravel()
        #print( "node IDs: " + str(nodeids) )

        channel_dtype = np.dtype( [ ( 'data', '<f4', (1, n_nodes ) ) ] )
        channel_data = np.fromfile( bin_file, dtype=channel_dtype )
        channel_data = channel_data['data'].reshape(n_tstep, n_nodes)

    raw_data = {'n_nodes': n_nodes,
                'n_tstep': n_tstep,
                'nodeids': nodeids,
                'data': channel_data}
    return raw_data
        
def loaddata(fname) :

    with open(fname) as fin :
        data = json.loads(fin.read())
        return data

def get_paths_hpc(settings, iteration) :

    sites = settings['sites'].keys()

    samples = load_samples(settings, iteration)
    paramnames = list(samples.columns.values)
    numsamples = len(samples[paramnames[0]].values)
    
    sim_map = createSimDirectoryMap(settings)

    for sim_key in sim_map :
        site = sim_map[sim_key]['_site_']
        for p in range(numsamples) :
            for run_num in range(settings['sim_runs_per_param_set']) :
                match = True
                for pname in paramnames :
                    if abs(sim_map[sim_key][pname] - samples[pname].values[p]) > settings['ERROR'] :
                        match = False
                        break
                if sim_map[sim_key]['Run_Number'] != run_num :
                    match = False
                if match :
                    samples.ix[p, site + ' outpath ' + str(run_num)] = sim_map[sim_key]['output_path']
                    break

    return samples

def get_paths_local(settings, iteration) :

    sites = settings['sites'].keys()

    samples = load_samples(settings, iteration)
    paramnames = list(samples.columns.values)
    numsamples = len(samples[paramnames[0]].values)

    sim_json_fname = settings['curr_iteration_dir'] + 'sim.json'
    with open(sim_json_fname) as fin :
        t = json.loads(fin.read())
        exp_id = t['exp_id']
        exp_name = t['exp_name']
        subdirs = t['sims'].keys()

    for sindex in range(len(subdirs)) :
        config_params = t['sims'][subdirs[sindex]]
        site = config_params['_site_']
        for p in range(numsamples) :
            for run_num in range(settings['sim_runs_per_param_set']) :
                match = True
                for pname in paramnames :
                    if abs(config_params[pname] - samples[pname].values[p]) > settings['ERROR'] :
                        match = False
                        break
                if config_params['Run_Number'] != run_num :
                    match = False
                if match :
                    samples.ix[p, site + ' outpath ' + str(run_num)] = settings['local_sim_root'] + exp_name + '_' + exp_id + '\\' + subdirs[sindex]
                    break

    return samples

def get_directories_local(settings) :

    sim_json_fname = settings['curr_iteration_dir'] + 'sim.json'
    with open(sim_json_fname) as fin :
        t = json.loads(fin.read())
        exp_id = t['exp_id']
        exp_name = t['exp_name']
        subdirs = t['sims'].keys()

    subdirpaths = []
    for subdir in subdirs :
        subdirpaths.append(settings['local_sim_root'] + exp_name + '_' + exp_id + '\\' + subdir)

    return subdirpaths
    
def createSimDirectoryMap(settings):

    with open(settings['curr_iteration_dir'] + 'sim.json') as fin :
        t = json.loads(fin.read())
        exp_id = t['exp_id']
        sim_pars = t['sims']

    from dtk.utils.simulation.OutputParser import CompsDTKOutputParser
    from COMPS import Client
    Client.Login('https://comps.idmod.org')
    sim_map = CompsDTKOutputParser.createSimDirectoryMap(exp_id=exp_id)

    for sim_id in sim_map :
        sim_pars[sim_id]['output_path'] = sim_map[sim_id]
    return sim_pars