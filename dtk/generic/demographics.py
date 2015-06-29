import os
import json

params = {
    "Demographics_Filenames": [],

    "Population_Scale_Type": "FIXED_SCALING",
    "Base_Population_Scale_Factor": 1,

    "Enable_Aging": 1,
    "Age_Initialization_Distribution_Type": "DISTRIBUTION_SIMPLE",

    "Enable_Demographics_Birth": 1,
    "Enable_Demographics_Gender": 1,
    "Enable_Demographics_Initial": 1,
    "Enable_Demographics_Other": 1,
    "Enable_Demographics_Reporting": 0,

    "Enable_Immunity_Initialization_Distribution": 0,

    "Enable_Vital_Dynamics": 1,
    "Death_Rate_Dependence": "NONDISEASE_MORTALITY_BY_AGE_AND_GENDER",
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

distribution_types = {
    "CONSTANT_DISTRIBUTION" : 0,
    "UNIFORM_DISTRIBUTION" : 1,
    "GAUSSIAN_DISTRIBUTION" : 2,
    "EXPONENTIAL_DISTRIBUTION" : 3,
    "POISSON_DISTRIBUTION" : 4,
    "LOG_NORMAL" : 5,
    "BIMODAL_DISTRIBUTION" : 6
    }

def set_risk_mod(filename, distribution, par1, par2):
    set_demog_distributions(filename, [("Risk", distribution, par1, par2)])

def set_immune_mod(filename, distribution, par1, par2):
    set_demog_distributions(filename, [("Immunity", distribution, par1, par2)])

def apply_to_defaults_or_nodes(demog, fn, *args):
    # distributions may be in Defaults or in Nodes list
    if "Defaults" in demog and "IndividualAttributes" in demog["Defaults"]:
        fn(demog["Defaults"],*args)
    else:
        for node in demog["Nodes"]:
            fn(node,*args)

def set_demog_distributions(filename, distributions):

    with open( filename, "r" ) as demogjson_file:
        demog = json.loads( demogjson_file.read() )

    def set_attributes(d,dist_type,par1,par2):
        d['IndividualAttributes'].update(
            {dist_type + "DistributionFlag": distribution_types[distribution],
             dist_type + "Distribution1": par1,
             dist_type + "Distribution2": par2})

    for (dist_type, distribution, par1, par2) in distributions:
        if distribution not in distribution_types.keys():
            raise Exception("Don't recognize distribution type %s" % distribution)

        apply_to_defaults_or_nodes(demog,set_attributes,dist_type,par1,par2)

    with open( filename, "w" ) as output_file:
        output_file.write( json.dumps( demog, sort_keys=True, indent=4 ) )

def set_static_demographics(cb, use_existing=False):

    demog_filenames = cb.get_param('Demographics_Filenames')
    if len(demog_filenames) != 1:
        raise Exception('Expecting only one demographics filename.')
    demog_filename = demog_filenames[0]
    static_demog_filename = demog_filename.replace("compiled.", "").replace(".json", ".static.json", 1)
    cb.set_param("Demographics_Filenames", [static_demog_filename])
    cb.set_param("Birth_Rate_Dependence", "FIXED_BIRTH_RATE")

    if use_existing:
        return

    with open( demog_filename, "r" ) as demogjson_file:
        demog = json.loads( demogjson_file.read() )

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

    def set_attributes(d):
        d['IndividualAttributes'].update(
            {"MortalityDistribution": mod_mortality,
             "AgeDistributionFlag": distribution_types["EXPONENTIAL_DISTRIBUTION"],
             "AgeDistribution1": exponential_age_param})
        d['NodeAttributes'].update({"BirthRate": birthrate})

    apply_to_defaults_or_nodes(demog,set_attributes)

    output_file_path = demog_filename.replace(".json",".static.json",1)
    with open( output_file_path, "w" ) as output_file:
        output_file.write( json.dumps( demog, sort_keys=True, indent=4 ) )

def set_growing_demographics(cb,use_existing=False):

    demog_filenames=cb.get_param('Demographics_Filenames')
    if len(demog_filenames)!=1:
        raise Exception('Expecting only one demographics filename.')
    demog_filename=demog_filenames[0]
    growing_demog_filename=demog_filename.replace("compiled.","").replace(".json",".growing.json",1)
    cb.set_param("Demographics_Filenames",[growing_demog_filename])
    cb.set_param("Birth_Rate_Dependence","POPULATION_DEP_RATE")

    if use_existing:
        return

    with open( demog_filename, "r" ) as demogjson_file:
        demog = json.loads( demogjson_file.read() )

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

    def set_attributes(d):
        d['IndividualAttributes'].update({"MortalityDistribution": mod_mortality})
        d['NodeAttributes'].update({"BirthRate": birthrate})

    apply_to_defaults_or_nodes(demog,set_attributes)

    output_file_path = demog_filename.replace(".json",".growing.json",1)
    with open( output_file_path, "w" ) as output_file:
        output_file.write( json.dumps( demog, sort_keys=True, indent=4 ) )
