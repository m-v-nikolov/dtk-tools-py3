import os
import json
import subprocess
import sys
from dtk.tools.demographics.compiledemog import CompileDemographics
from dtk.generic.geography import geographies


params = {
    "Demographics_Filename": "", 

    "Population_Scale_Type": "FIXED_SCALING", 
    "Base_Population_Scale_Factor": 1, 

    "Enable_Aging": 1, 
    "Age_Initialization_Distribution_Type": "DISTRIBUTION_SIMPLE", 

    "Enable_Demographics_Birth": 1, 
    "Enable_Demographics_Gender": 1, 
    "Enable_Demographics_Initial": 1, 
    "Enable_Demographics_Other": 1, 
    "Enable_Demographics_Reporting": 1, 

    "Enable_Immunity_Initialization_Distribution": 0, 

    "Enable_Vital_Dynamics": 1, 
    "Enable_Nondisease_Mortality": 1, 
    "Enable_Birth": 1, 
    "Birth_Rate_Dependence": "POPULATION_DEP_RATE", 
    "x_Birth": 1, 

    "Enable_Disease_Mortality": 0, 
    "Base_Mortality": 0, 
    "Mortality_Time_Course": "DAILY_MORTALITY",
    "x_Other_Mortality": 1, 

    "Individual_Sampling_Type": "TRACK_ALL", 
    "Base_Individual_Sample_Rate": 1,  ## all parameters below are unused without sampling
    "Max_Node_Population_Samples": 40, 
    "Sample_Rate_0_18mo": 1, 
    "Sample_Rate_10_14": 1, 
    "Sample_Rate_15_19": 1, 
    "Sample_Rate_18mo_4yr": 1, 
    "Sample_Rate_20_Plus": 1, 
    "Sample_Rate_5_9": 1, 
    "Sample_Rate_Birth": 2
}

def set_risk_mod(filename, distribution, par1, par2):
    set_demog_distributions(filename, [("Risk", distribution, par1, par2)])

def set_immune_mod(filename, distribution, par1, par2):
    set_demog_distributions(filename, [("Immunity", distribution, par1, par2)])

def set_demog_distributions(filename, distributions):

    with open( filename, "r" ) as demogjson_file:
        demog = json.loads( demogjson_file.read() )

    distribution_types = { 
        "CONSTANT_DISTRIBUTION" : 0,
        "UNIFORM_DISTRIBUTION" : 1,
        "GAUSSIAN_DISTRIBUTION" : 2,
        "EXPONENTIAL_DISTRIBUTION" : 3,
        "POISSON_DISTRIBUTION" : 4,
        "LOG_NORMAL" : 5,
        "BIMODAL_DISTRIBUTION" : 6
        }

    for (dist_type, distribution, par1, par2) in distributions:
        if distribution not in distribution_types.keys():
            raise Exception("Don't recognize distribution type %s" % distribution)

        # distributions may be in Nodes list or Defaults
        if "Defaults" in demog and "IndividualAttributes" in demog["Defaults"]:
            demog["Defaults"]["IndividualAttributes"][dist_type + "DistributionFlag"] = distribution_types[distribution]
            demog["Defaults"]["IndividualAttributes"][dist_type + "Distribution1"] = par1
            demog["Defaults"]["IndividualAttributes"][dist_type + "Distribution2"] = par2
        else:
            for node in demog["Nodes"]:
                node["IndividualAttributes"][dist_type + "DistributionFlag"] = distribution_types[distribution]
                node["IndividualAttributes"][dist_type + "Distribution1"] = par1
                node["IndividualAttributes"][dist_type + "Distribution2"] = par2

    # write
    with open( filename, "w" ) as output_file:
        output_file.write( json.dumps( demog, sort_keys=True, indent=4 ) )

# Static demographics
def set_static_demographics(input_path, config, recompile=False):

    if not recompile:
        config["parameters"]["Birth_Rate_Dependence"] = "FIXED_BIRTH_RATE"
        config["parameters"]["Demographics_Filename"] = config["parameters"]["Demographics_Filename"].replace("demographics","demographics.static",1)
        return config

    # get demographics file
    demog_filename = config["parameters"]["Demographics_Filename"].replace("compiled.","",1)
    with open( os.path.join(input_path, demog_filename), "r" ) as demogjson_file:
        demog = json.loads( demogjson_file.read() )

    # set birth rate (by population) and death rate
    config["parameters"]["Birth_Rate_Dependence"] = "FIXED_BIRTH_RATE"
    birthrate = 0.12329
    exponential_age_param = 0.000118
    population_removal_rate = 45
    mod_mortality = {
                    "NumDistributionAxes": 2,
                    "AxisNames": [ "gender", "age" ],
                    "AxisUnits": [ "male=0,female=1", "years" ],
                    "AxisScaleFactors": [ 1, 365 ],
                    "NumPopulationGroups": [ 2, 1 ],
                    "PopulationGroups": [
                        [ 0, 1 ],
                        [ 0 ]
                    ],
                    "ResultUnits": "annual deaths per 1000 individuals",
                    "ResultScaleFactor": 2.74e-06,
                    "ResultValues": [
                        [ population_removal_rate ],
                        [ population_removal_rate ]
                    ]
                }

    # distributions may be in Nodes list or Defaults
    if "Defaults" in demog and "IndividualAttributes" in demog["Defaults"]:
        demog["Defaults"]["IndividualAttributes"]["MortalityDistribution"].update(mod_mortality)
        demog["Defaults"]["IndividualAttributes"]["AgeDistribution1"] = exponential_age_param
        demog["Defaults"]["NodeAttributes"]["BirthRate"] = birthrate
    else:
        for node in demog["Nodes"]:
            node["IndividualAttributes"]["MortalityDistribution"].update(mod_mortality)
            node["IndividualAttributes"]["AgeDistribution1"] = exponential_age_param
            node["NodeAttributes"]["BirthRate"] = birthrate

    # write
    output_file_path = os.path.join( input_path, demog_filename.replace(".json",".static.json",1))
    with open( output_file_path, "w" ) as output_file:
        output_file.write( json.dumps( demog, sort_keys=True, indent=4 ) )

    # compile
    CompileDemographics(output_file_path, forceoverwrite=True)
    config["parameters"]["Demographics_Filename"] = config["parameters"]["Demographics_Filename"].replace("demographics","demographics.static",1)

    return config

# Realistic growing population demographics
def set_realistic_demographics(input_path, config, recompile=False):

    if not recompile:
        config["parameters"]["Birth_Rate_Dependence"] = "POPULATION_DEP_RATE"
        config["parameters"]["Demographics_Filename"] = config["parameters"]["Demographics_Filename"].replace("demographics","demographics.pop_growth",1)
        return config

    # get demographics file
    demog_filename = config["parameters"]["Demographics_Filename"].replace("compiled.","",1)
    with open( os.path.join(input_path, demog_filename), "r" ) as demogjson_file:
        demog = json.loads( demogjson_file.read() )

    # set birth rate (by population) and death rate
    config["parameters"]["Birth_Rate_Dependence"] = "POPULATION_DEP_RATE"
    birthrate = 0.0001
    mod_mortality = {
                    "NumDistributionAxes": 2,
                    "AxisNames": [ "gender", "age" ],
                    "AxisUnits": [ "male=0,female=1", "years" ],
                    "AxisScaleFactors": [ 1, 365 ],
                    "NumPopulationGroups": [ 2, 5 ],
                    "PopulationGroups": [
                        [ 0, 1 ],
                        [ 0, 2, 10, 100, 2000 ]
                    ],
                    "ResultUnits": "annual deaths per 1000 individuals",
                    "ResultScaleFactor": 2.74e-06,
                    "ResultValues": [
                        [ 60, 8, 2, 20, 400 ],
                        [ 60, 8, 2, 20, 400 ]
                    ]
                }

    # distributions may be in Nodes list or Defaults
    if "Defaults" in demog and "IndividualAttributes" in demog["Defaults"]:
        demog["Defaults"]["IndividualAttributes"]["MortalityDistribution"].update(mod_mortality)
        demog["Defaults"]["NodeAttributes"]["BirthRate"] = birthrate
    else:
        for node in demog["Nodes"]:
            node["IndividualAttributes"]["MortalityDistribution"].update(mod_mortality)
            node["NodeAttributes"]["BirthRate"] = birthrate

    # write
    output_file_path = os.path.join( input_path, demog_filename.replace(".json",".pop_growth.json",1))
    with open( output_file_path, "w" ) as output_file:
        output_file.write( json.dumps( demog, sort_keys=True, indent=4 ) )

    # compile
    CompileDemographics(output_file_path, forceoverwrite=True)
    config["parameters"]["Demographics_Filename"] = config["parameters"]["Demographics_Filename"].replace("demographics","demographics.pop_growth",1)

    return config

def add_immune_overlays(cb, tags):

    demog_filename = cb.get_param("Demographics_Filename")

    if len(demog_filename.split(';')) > 1:
        raise Exception('add_immune_init function is expecting only a single demographics file.  Not a semi-colon-delimited list.')
    split_demog = demog_filename.split('.')
    prefix,suffix = split_demog[0],split_demog[1:]

    demogfiles = [demog_filename]
    for tag in tags:
        if 'demographics' not in prefix:
            raise Exception('add_immune_init function expecting a base demographics layer with demographics in the name.')
        immune_init_file_name = prefix.replace("demographics","immune_init_" + tag, 1) + "."+suffix[0]
        demogfiles.append(immune_init_file_name)

    cb.update_params({ "Enable_Immunity_Initialization_Distribution":1,
                       "Demographics_Filename": ';'.join(demogfiles) })
    
    
    

# Immune initialization based on habitat scaling
def add_immune_init(cb, site, x_temp_habitats):
    tags = []
    for x_temp_habitat in x_temp_habitats:
        tags.append( "x_" + str(x_temp_habitat) )
    add_immune_overlays(cb, tags)