from dtk.utils.core.DTKSetupParser import DTKSetupParser
from dtk.utils.parsers.JSON import json2dict

params = {
    "Antibody_CSP_Decay_Days": 90,
    "Antibody_CSP_Killing_Inverse_Width": 1.5,
    "Antibody_CSP_Killing_Threshold": 20,

    "Innate_Immune_Variation_Type": "NONE",
    "Pyrogenic_Threshold": 1.5e4,
    "Fever_IRBC_Kill_Rate": 1.4,

    "Max_MSP1_Antibody_Growthrate": 0.045,
    "Antibody_Capacity_Growth_Rate": 0.09,
    "Nonspecific_Antibody_Growth_Rate_Factor": 0.5, # multiplied by major-epitope number to get rate
    "Antibody_Stimulation_C50": 30,
    "Antibody_Memory_Level": 0.34,
    "Min_Adapted_Response": 0.05,

    "Cytokine_Gametocyte_Inactivation": 0.01667,

    "Maternal_Antibodies_Type": "SIMPLE_WANING",
    "Maternal_Antibody_Protection": 0.1327,
    "Maternal_Antibody_Decay_Rate": 0.01,

    "Erythropoiesis_Anemia_Effect": 3.5
    }

def add_immune_overlays(cb, tags, directory=DTKSetupParser().get('LOCAL','input_root')):

    demogfiles = cb.get_param("Demographics_Filenames")

    if len(demogfiles) != 1:
        raise Exception('add_immune_init function is expecting only a single demographics file.')

    demog_filename=demogfiles[0]
    prefix = demog_filename.split('.')[0]

    if 'demographics' not in prefix:
        raise Exception('add_immune_init function expecting a base demographics layer with demographics in the name.')

    for tag in tags:
        immune_init_name = prefix.replace("demographics","immune_init_" + tag, 1)
        if directory:
            cb.add_demog_overlay(immune_init_name,json2dict(os.path.join(directory,'%s.json'%immune_init_name)))
        else:
            cb.append_overlay('%s.json'%immune_init_name)

    cb.set_param("Enable_Immunity_Initialization_Distribution",1)

# Immune initialization based on habitat scaling
def add_immune_init(cb, site, x_temp_habitats, directory=None):
    tags = ["x_"+str(x) for x in x_temp_habitats]
    add_immune_overlays(cb, tags, directory)
