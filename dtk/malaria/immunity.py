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

def add_immune_overlays(cb, tags):

    demogfiles = cb.get_param("Demographics_Filenames")

    if len(demogfiles) > 1:
        raise Exception('add_immune_init function is expecting only a single demographics file.')

    demog_filename=demogfiles[0]
    split_demog = demog_filename.split('.')
    prefix,suffix = split_demog[0],split_demog[1:]

    for tag in tags:
        if 'demographics' not in prefix:
            raise Exception('add_immune_init function expecting a base demographics layer with demographics in the name.')
        immune_init_file_name = prefix.replace("demographics","immune_init_" + tag, 1) + "."+suffix[0]
        demogfiles.append(immune_init_file_name)

    cb.update_params({ "Enable_Immunity_Initialization_Distribution":1,
                       "Demographics_Filenames": demogfiles })

# Immune initialization based on habitat scaling
def add_immune_init(cb, site, x_temp_habitats):
    tags = []
    for x_temp_habitat in x_temp_habitats:
        tags.append( "x_" + str(x_temp_habitat) )
    add_immune_overlays(cb, tags)
