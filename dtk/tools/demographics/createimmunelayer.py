import json
import os
import scipy # for calculating means

from dtk.utils.core.DTKSetupParser import DTKSetupParser
input_path = DTKSetupParser().get('LOCAL','input_root')

br_channel_titles = ["MSP", "Non-Specific", "PfEMP1"]
output_channel_titles = ["MSP", "nonspec", "PfEMP1"]

def make_template_from_demographics(demog_json):
    print('Cleaning base demographics for immune init overlay')

    # Implicitly keeping the Metadata block if that is included

    # Keeping only the NodeID property for each node
    if "Nodes" in demog_json:
        for node in demog_json["Nodes"]:
            
            if "IndividualAttributes" in node.keys():
                node.pop("IndividualAttributes") 
            if "NodeAttributes" in node.keys():
                node.pop("NodeAttributes") 

    # Replace "Defaults" with these empty blocks
    demog_json["Defaults"] = {  "MSP_mean_antibody_distribution"         : {},
                                "nonspec_mean_antibody_distribution"     : {},
                                "PfEMP1_mean_antibody_distribution"      : {},
                                "MSP_variance_antibody_distribution"     : {},
                                "nonspec_variance_antibody_distribution" : {},
                                "PfEMP1_variance_antibody_distribution"  : {}  }

def bin_centers_from_upper_bounds(agebins, norm=365.0):
    pop_groups = [0] # needs extra zero since there are n_ages + 1 bins in demographics layer
    lastage=0
    for age in agebins:
        pop_groups.append((age/norm + lastage)/2)
        lastage = age/norm
    pop_groups[-1] = pop_groups[-2] + 25 # A bit of a hack for assigning a bin-center when the upper bound can be 1000 years old
    return pop_groups

def insert_immunity_distribution_metadata(demog_json, pop_groups):
    for k,v in demog_json["Defaults"].items():
        v = { "NumDistributionAxes": 1,
                "AxisNames": [ "age" ],
                "AxisUnits": [ "years" ],
                "AxisScaleFactors": [ 365 ],
                "NumPopulationGroups": [ len(pop_groups) ],
                "PopulationGroups": [ pop_groups ],
                "ResultUnits": "mean fraction of antibody variants",
                "ResultScaleFactor": 1,
                "ResultValues": []
                }
        demog_json["Defaults"][k] = v

def mean_and_std_from_binned_report(br_json, antibody_type_idx):
    Ab_mean_results = [0] # needs extra zero since there are n_ages + 1 bins in demographics layer
    Ab_std_results  = [0]

    age_bins = br_json["Header"]["Subchannel_Metadata"]["NumBinsPerAxis"][0][0]

    for age_idx in range(0,age_bins):
        Ab        = br_json["Channels"]["Sum " + br_channel_titles[antibody_type_idx] + " Variant Fractions"]["Data"][age_idx][-365:]
        ss_Ab     = br_json["Channels"]["Sum of Squared " + br_channel_titles[antibody_type_idx] + " Variant Fractions"]["Data"][age_idx][-365:]
        statpop   = br_json["Channels"]["Population"]["Data"][age_idx][-365:]

        mean_Ab = []
        std_Ab  = []
        for val,ss,pop in zip(Ab,ss_Ab,statpop):
            if pop > 0:
                mean = val/pop
                variance = ss/pop - mean**2
            else:
                mean = 0
                variance = 0
            mean_Ab.append(mean)
            if variance < 0:
                std_Ab.append(0)
            else:
                std_Ab.append(variance**0.5)

        #print(scipy.mean(mean_Ab), scipy.mean(std_Ab))
        Ab_mean_results.append(scipy.mean(mean_Ab))
        Ab_std_results.append(scipy.mean(std_Ab))

    return (Ab_mean_results, Ab_std_results)
'''
def immune_init_overlays_from_burnin_sweep(metadata):

    config_names = set([])
    output_path = metadata['sim_root']
    expId = metadata['expId']

    for simId, sim in metadata['sims'].items():

        ConfigName = sim['Config_Name']
        demog_name = sim['Demographics_Filename']

        # TODO: actually combine different runs to get average immune initialization?
        # For now we just use the first burnin-simulation by unique ConfigName and skip over subsequent repeats
        if ConfigName in config_names:
            print('Already have %s' % ConfigName)
            continue
        else:
            print('Adding %s' % ConfigName)
            config_names.update([ConfigName])

        binned_report_path = os.path.join(output_path, expId, simId)
        immune_init_from_binned_report(demog_name, binned_report_path, ConfigName)


def immune_init_from_binned_report(demog_name, binned_report_path, ConfigName, doWrite=True, doCompile=True):

    # copy and modify values
    print('Loading demographics')
    with open( os.path.join( input_path, demog_name.replace('compiled.','') ) ) as demog_json_file:
        demog_json = json.loads( demog_json_file.read() )

    make_template_from_demographics(demog_json)

    print('Loading binned report')
    with open( os.path.join( binned_report_path, "output", "BinnedReport.json") ) as br_json_file:
        br_json = json.loads( br_json_file.read() )

    pop_groups = bin_centers_from_upper_bounds(br_json["Header"]["Subchannel_Metadata"]["ValuesPerAxis"][0][0], norm=365.0)

    insert_immunity_distribution_metadata(demog_json, pop_groups)

    print('Extracting antibody distributions and inserting into immune overlay')
    for antibody_type_idx in range(0,len(output_channel_titles)):
        (Ab_mean_results, Ab_std_results) = mean_and_std_from_binned_report(br_json, antibody_type_idx)
        demog_json["Defaults"][output_channel_titles[antibody_type_idx] + "_mean_antibody_distribution"]["ResultValues"]     = Ab_mean_results
        demog_json["Defaults"][output_channel_titles[antibody_type_idx] + "_variance_antibody_distribution"]["ResultValues"] = Ab_std_results

    if doWrite:
        immune_overlay_name = ('.'.join(demog_name.split('.')[:-1])).replace('demographics.compiled','immune_init_') + ConfigName + '.json'
        output_file_name = os.path.join(input_path, immune_overlay_name)
        print(output_file_name)
        with open( output_file_name, 'w' ) as f:
            f.write( json.dumps( demog_json, sort_keys=True, indent=4 ) )

        if doCompile:
            CompileDemographics(output_file_name, forceoverwrite=True)
    else:
        print(json.dumps(demog_json,sort_keys=True,indent=4))

def immune_init_from_custom_output(demog_json, custom_output_file, ConfigName, BaseName='TEST', site='', doWrite=True, doCompile=True):

    make_template_from_demographics(demog_json)
    print('Loading MalariaImmunityReport')
    with open(custom_output_file) as immunity_report:
        ir_json = json.loads( immunity_report.read() )
    pop_groups = bin_centers_from_upper_bounds(ir_json['Age Bins'], norm=1.0) # these are ages in years already
    insert_immunity_distribution_metadata(demog_json, pop_groups)

    print('Extracting antibody distributions and inserting into immune overlay')
    for antibody_type_idx in range(0,len(output_channel_titles)):
        # needs extra zero since there are n_ages + 1 bins in demographics layer
        demog_json["Defaults"][output_channel_titles[antibody_type_idx] + "_mean_antibody_distribution"]["ResultValues"]     = [0] + ir_json[br_channel_titles[antibody_type_idx] + ' Mean by Age Bin'][-1]
        demog_json["Defaults"][output_channel_titles[antibody_type_idx] + "_variance_antibody_distribution"]["ResultValues"] = [0] + ir_json[br_channel_titles[antibody_type_idx] + ' StdDev by Age Bin'][-1]

    if doWrite:
        immune_overlay_name = BaseName.replace('demographics', 'immune_init_' + ConfigName, 1)
        subdirs, immune_overlay_name = os.path.split(immune_overlay_name)
        output_dir = os.path.join(input_path, subdirs, 'immune_init', site)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file_name = os.path.join(output_dir, immune_overlay_name)
        print(output_file_name)
        with open( output_file_name, 'w' ) as f:
            f.write( json.dumps( demog_json, sort_keys=True, indent=4 ) )

        if doCompile:
            CompileDemographics(output_file_name, forceoverwrite=True)
    else:
        print(json.dumps(demog_json,sort_keys=True,indent=4))
'''        

def immune_init_from_custom_output_for_spatial(demog_json, custom_output_file):

    make_template_from_demographics(demog_json)

    with open(custom_output_file) as immunity_report:
        ir_json = json.loads( immunity_report.read() )
    pop_groups = bin_centers_from_upper_bounds(ir_json['Age Bins'], norm=1.0) # these are ages in years already
    insert_immunity_distribution_metadata(demog_json, pop_groups)

    print('Extracting antibody distributions and inserting into immune overlay')
    for antibody_type_idx in range(0,len(output_channel_titles)):
        # needs extra zero since there are n_ages + 1 bins in demographics layer
        demog_json["Defaults"][output_channel_titles[antibody_type_idx] + "_mean_antibody_distribution"]["ResultValues"]     = [0] + ir_json[br_channel_titles[antibody_type_idx] + ' Mean by Age Bin'][-1]
        demog_json["Defaults"][output_channel_titles[antibody_type_idx] + "_variance_antibody_distribution"]["ResultValues"] = [0] + ir_json[br_channel_titles[antibody_type_idx] + ' StdDev by Age Bin'][-1]

    return demog_json

if __name__ == "__main__":

    # For running from FarEastTower on Sabalcore, where PYTHONPATH doesn't have dtk package
    #import sys
    #sys.path.append('C:/Users/jgerardin/SVN/python')
    #from dtk.utils.compiledemog import CompileDemographics

    ##  Example #1
    ##  Generate immune overlay for a single input demographics file and output directory of sim with BinnedReport
    #'''
    demog_name = "Burkina Faso_Dapelogo_2.5arcmin_demographics.compiled.json"
    output_path = "Z:/output/simulations/ImmuneInit"
    expId = "ImmuneInitx0.1_2014_10_21_15_21_09_707000"
    simId = "3c3/a77/458/3c3a7745-8f59-e411-93f6-f0921c16b9e0"
    binned_report_path = os.path.join(output_path, expId, simId)
    ConfigName = "Dapelogo_x_0.1"
    #immune_init_from_binned_report(demog_name, binned_report_path, ConfigName)
    #'''

    ## Example #2
    ## Generate immune overlays for all unique ConfigNames in burnin sweep experiment
    '''
    with open("D:/ewenger/sanity_checking_kevins_calibrations/simulations/burnin_expId_2013_11_18_11_56_00_015000.json") as metadata_file:
        metadata = json.loads(metadata_file.read())
    immune_init_overlays_from_burnin_sweep(metadata)
    '''

    ## Example #3
    ## Generate immune overlay with empty Nodes block based on MalariaImmuneReport output
    '''
    immunity_report_path = 'D:/EMOD/simulations_local/inputEIR_expId_2014_02_11_15_31_38_465000/simId_2014_02_11_15_31_38_580000/output'
    immune_init_from_custom_output({'Nodes':[], 'Metadata':{}}, 
                                   os.path.join(immunity_report_path, 'MalariaImmunityReport_BirthCohortAverage.json'), 
                                   'Ndiop_x_1.0', doWrite=True, doCompile=False)
    '''

    ## Example #4
    ## Generate immune overlays from MalariaImmuneReport output in sweep
    '''
    with open("D:/malaria/zambia/dtk/1node/simulations/inputEIR_expId_2014_02_11_15_47_26_844000.json") as metadata_file:
        metadata = json.loads(metadata_file.read())
    output_path = metadata['sim_root']
    expId = metadata['expId']
    for simId, sim in metadata['sims'].items():
        ConfigName = sim['Config_Name']
        demog_name = sim['Demographics_Filename']
        immunity_report_path = os.path.join(output_path, expId, simId)
        immune_init_from_custom_output({ "Metadata": { "Author": "ewenger", 
                                                       "IdReference": "Gridded world grump2.5arcmin", 
                                                       "NodeCount": 1 }, 
                                         "Nodes": [ { "NodeID": 326436567 } ] }, 
                                       os.path.join(immunity_report_path, 'output', 'MalariaImmunityReport_BirthCohortAverage.json'), 
                                       ConfigName, doWrite=True, doCompile=False)
    '''
    '''
    with open("D:/malaria/zambia/dtk/1node/simulations/burnin_expId_2014_03_11_11_42_17_747000.json") as metadata_file:
        metadata = json.loads(metadata_file.read())
    output_path = metadata['sim_root']
    expId = metadata['expId']
    for simId, sim in metadata['sims'].items():
        ConfigName = sim['Config_Name']
        demog_name = sim['Demographics_Filename']
        immunity_report_path = os.path.join(output_path, expId, simId)
        immune_init_from_custom_output({ "Metadata": { "Author": "ewenger", 
                                                       "IdReference": "Gridded world grump2.5arcmin", 
                                                       "NodeCount": 1 }, 
                                         "Nodes": [ { "NodeID": 326436567 } ] }, 
                                       os.path.join(immunity_report_path, 'output', 'MalariaImmunityReport_FinalYearAverage.json'), 
                                       ConfigName, BaseName=demog_name.split('.')[0].replace('_demographics',''), doWrite=True, doCompile=True)
    '''