import os, json, subprocess, sys
from dtk.tools.demographics.compiledemog import CompileDemographics

def set_risk_mod(filename, distribution, par1, par2):
    set_demog_distributions(filename, [("Risk", distribution, par1, par2)])

def set_immune_mod(filename, distribution, par1, par2):
    set_demog_distributions(filename, [("Immunity", distribution, par1, par2)])

def set_demog_distributions(filename, distributions):

    demogjson_file = open( filename, "r" )
    demog = json.loads( demogjson_file.read() )
    demogjson_file.close()

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
    output_file = open( filename, "w" )
    output_file.write( json.dumps( demog, sort_keys=True, indent=4 ) )
    output_file.close()

    # compile
    CompileDemographics(filename, forceoverwrite=True)

# Static demographics
def set_static_demographics(input_path, config, geography, recompile=True):

    if not recompile:
        config["parameters"]["Birth_Rate_Dependence"] = "FIXED_BIRTH_RATE"
        config["parameters"]["Demographics_Filename"] = config["parameters"]["Demographics_Filename"].replace("demographics","demographics.static",1)
        return config

    # get demographics file
    demog_filename = config["parameters"]["Demographics_Filename"].replace("compiled.","",1)
    demogjson_file = open( os.path.join(input_path, geography, demog_filename), "r" )
    demog = json.loads( demogjson_file.read() )
    demogjson_file.close()

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
    output_file_path = os.path.join( input_path, geography, demog_filename.replace(".json",".static.json",1))
    output_file = open( output_file_path, "w" )
    output_file.write( json.dumps( demog, sort_keys=True, indent=4 ) )
    output_file.close()

    # compile
    CompileDemographics(output_file_path, forceoverwrite=True)
    config["parameters"]["Demographics_Filename"] = config["parameters"]["Demographics_Filename"].replace("demographics","demographics.static",1)

    return config


# Realistic growing population demographics
def set_realistic_demographics(input_path, config, geography, recompile=True):

    if not recompile:
        config["parameters"]["Birth_Rate_Dependence"] = "POPULATION_DEP_RATE"
        config["parameters"]["Demographics_Filename"] = config["parameters"]["Demographics_Filename"].replace("demographics","demographics.pop_growth",1)
        return config

    # get demographics file
    demog_filename = config["parameters"]["Demographics_Filename"].replace("compiled.","",1)
    demogjson_file = open( os.path.join(input_path, geography, demog_filename), "r" )
    demog = json.loads( demogjson_file.read() )
    demogjson_file.close()

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
    output_file_path = os.path.join( input_path, geography, demog_filename.replace(".json",".pop_growth.json",1))
    output_file = open( output_file_path, "w" )
    output_file.write( json.dumps( demog, sort_keys=True, indent=4 ) )
    output_file.close()

    # compile
    CompileDemographics(output_file_path, forceoverwrite=True)
    config["parameters"]["Demographics_Filename"] = config["parameters"]["Demographics_Filename"].replace("demographics","demographics.pop_growth",1)

    return config

def add_immune_overlays(input_path, geography, config, tags):

    demog_filename = config["parameters"]["Demographics_Filename"]
    demog_prefix = demog_filename.split('.')[0]
    #print(demog_filename)
    if len(demog_filename.split(';')) > 1:
        raise Exception('add_immune_init function is expecting only a single demographics file.  Not a semi-colon-delimited list.')

    demogfiles = [demog_filename]
    for tag in tags:
        #print(tag)
        if 'demographics' not in demog_prefix:
            raise Exception('add_immune_init function expecting a base demographics layer with demographics in the name.')
        immune_init_file_name = demog_prefix.replace("demographics","immune_init_" + tag, 1) + '.compiled.json'
        #print(immune_init_file_name)
        if not os.path.exists(os.path.join(input_path, geography, immune_init_file_name)):
            raise Exception('Immune initialization file ' + immune_init_file_name + ' does not exist at ' + os.path.join(input_path, geography))
        demogfiles.append(immune_init_file_name)

    full_demog_string = ';'.join(demogfiles)
    #print(full_demog_string)
    mod_params = { "Enable_Immunity_Initialization_Distribution":1,
                   "Demographics_Filename": full_demog_string
                  }
    config["parameters"].update(mod_params)
    return config

# Immune initialization based on habitat scaling
def add_immune_init(input_path, geography, config, site, x_temp_habitat):
    tags = [ str(site) + "_x_" + str(x_temp_habitat) ]
    add_immune_overlays(input_path, geography, config, tags)