import glob
import json
import os
import shutil
import sys
from copy import deepcopy as dcopy

from simtools.ExperimentManager import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.core.DTKSetupParser import DTKSetupParser
from dtk.vector.species import set_species_param, set_larval_habitat
from dtk.interventions.habitat_scale import scale_larval_habitats
from dtk.interventions.malaria_drug_campaigns import add_drug_campaign
from dtk.interventions.malaria_drugs import set_drug_param

from load_settings import load_all_settings
from next_parameters import update_params
from load_parameters import load_samples
from study_sites.set_calibration_site import set_calibration_site
from utils import check_for_done, update_settings, concat_likelihoods
from analyze import analyze
from visualize import visualize

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

    builders = list()

    # For each param = value, create a simulation
    for i in range(numvals) :
        vector_habitats_processed = False
        current_sim = list()
        for pname in samples.columns.values:
            # Get the value here
            val = str(samples[pname].values[i])
            try:
                pval = float(val)
            except:
                pval = val

            # Depending on whats in the parameter carry out different actions
            # CAMPAIGN shortcut
            if 'CAMPAIGN' in pname:
                cparam = pname.split('.')
                if cparam[1] == 'DRUG':
                    camp_code = cparam[2]
                    start_day = int(cparam[3])
                    current_sim.append(ModBuilder.ModFn(add_drug_campaign,drug_code=camp_code, start_days=[start_day], coverage=pval, repetitions=1))

            # HABSCALE shortcut
            elif 'HABSCALE' in pname:
                node = pname.split('.')[1]
                current_sim.append(ModBuilder.ModFn(scale_larval_habitats, scales=[([node],pval),] ))

            # DRUG
            elif 'DRUG' in pname:
                vname = pname.split('.')[1]
                vpar = pname.split('.')[2]
                current_sim.append(ModBuilder.ModFn(set_drug_param, drugname=vname, parameter=vpar , value=pval))

            # VECTOR shortcut
            elif 'VECTOR' in pname:
                vpar = pname.split('.')[2]
                if 'Required_Habitat_Factor' in vpar:
                    if not vector_habitats_processed:
                        # First time we encounter a required habitat => process all of them
                        # We have to still let the loop finish so when other habitats are encounter we still set them in the config file (use for the priors)
                        # Grab all the parameters with Required_Habitat_Factor in the name
                        vectors = dict()
                        for vec in [x for x in samples.columns.values if 'Required_Habitat_Factor' in x]:
                            # Retrieve the vector name
                            vname = vec.split('.')[1]
                            habname = vec.split('.')[3]

                            # If this vector doesnt exist in the dict -> create it
                            if not vectors.has_key(vname):
                                vectors[vname] = dict()

                            # Retrieve the value for the current vector/current habitat
                            vectors[vname][habname] = float(samples[vec].values[i])


                        # Set the flag to true to not redo the same thing over and over
                        vector_habitats_processed = True

                        # Add the builder
                        current_sim.append(ModBuilder.ModFn(set_larval_habitat, vectors))
                else :
                    vname = pname.split('.')[1]
                    current_sim.append(ModBuilder.ModFn(set_species_param, species=vname, parameter=vpar, value=pval))

            current_sim.append(ModBuilder.ModFn(DTKConfigBuilder.set_param,pname,pval))

        # For each sites and run_number, duplicate the simulation, add the site and add to the builder list
        for site in settings['sites']:
            for run_num in range(settings['sim_runs_per_param_set']) :
                current_sim_site = dcopy(current_sim)
                current_sim_site.append(ModBuilder.ModFn(set_calibration_site,site))
                current_sim_site.append(ModBuilder.ModFn(DTKConfigBuilder.set_param,'Run_Number',run_num))
                builders.append(current_sim_site)

    # Create the configbuilder
    builder = ModBuilder.from_list(builders)
    cb = DTKConfigBuilder.from_defaults('MALARIA_SIM')
    location = 'HPC' if 'hpc' in settings['run_location'].lower() else 'LOCAL'

    # Run the simulation
    sm = ExperimentManagerFactory.from_setup(DTKSetupParser(), location)
    sm.run_simulations(config_builder=cb, exp_name=settings['expname'], exp_builder=builder)

    # Get the latest experiment json of the folder simulations to find what is the current running experiment
    newest = max(glob.iglob('%s\\*.json' % os.path.join(settings['working_dir'],'simulations')), key=os.path.getctime)

    # Copy this newest in the sim.json
    shutil.copyfile(newest, os.path.join(settings['curr_iteration_dir'],'sim.json'))


if __name__ == '__main__':

    if len(sys.argv) > 1 :
        ofname = sys.argv[1]
        run(ofname)
    else :
        run('calibration_overlays.json')
