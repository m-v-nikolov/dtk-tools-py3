import os

from simtools.SetupParser import SetupParser
from dtk.utils.parsers.JSON import json2dict
from dtk.vector.study_sites import StudySite, set_habitat_scale

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

def add_immune_overlays(cb, tags, directory=SetupParser().get('LOCAL','input_root'), site=None):
    """
    Add an immunity overlay.

    To do so, reads the demographics files and find the corresponding immunity initialization overlay.

    :param cb: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` holding the configuration
    :param tags: List of immunity tags that have corresponding initialization files
    :param directory: Main directory where the ..._immune_init_x_...json files are stored
    :param site: If the site is specified, the files will be expected to be found in the immune_init/site subdirectory.
    :return: Nothing
    """

    demogfiles = cb.get_param("Demographics_Filenames")

    if len(demogfiles) != 1:
        print(demogfiles)
        raise Exception('add_immune_init function is expecting only a single demographics file.')

    demog_filename = demogfiles[0]

    subdirs, demog_filename = os.path.split(demog_filename)
    if '2.5' not in demog_filename :
        prefix = demog_filename.split('.')[0]
    else :
        prefix = '.'.join(demog_filename.split('.')[:2])

    # e.g. DataFiles/Zambia/Sinamalima_single_node/immune_init/SinazongweConstant/..._immune_init_x_...json
    if site:
        subdirs = os.path.join(subdirs, 'immune_init', site)

    if 'demographics' not in prefix:
        raise Exception('add_immune_init function expecting a base demographics layer with demographics in the name.')

    for tag in tags:
        immune_init_name = prefix.replace("demographics", "immune_init_" + tag, 1)
        if directory:
            cb.add_demog_overlay(immune_init_name, json2dict(os.path.join(directory, subdirs, '%s.json' % immune_init_name)))
        else:
            cb.append_overlay(os.path.join(subdirs, '%s.json' % immune_init_name))

    cb.enable("Immunity_Initialization_Distribution")  # compatibility with EMOD v2.0 and earlier
    cb.set_param("Immunity_Initialization_Distribution_Type", "DISTRIBUTION_COMPLEX")

def add_immune_init(cb, site, x_temp_habitats, directory=None):
    """
    Initializes the immunity based on habitat scaling.

    Simply create the tags and call the :any:`add_immune_overlays` function.

    :param cb: The :py:class:`DTKConfigBuilder <dtk.utils.core.DTKConfigBuilder>` holding the configuration
    :param site: If the site is specified, the files will be expected to be found in the immune_init/site subdirectory.
    :param x_temp_habitats: List of temp habitats
    :param directory: Main directory where the ..._immune_init_x_...json files are stored
    :return: Nothing
    """
    tags = ["x_" + str(x) for x in x_temp_habitats]
    add_immune_overlays(cb, tags, directory, site=site)

def scale_habitat_with_immunity(cb, available=[], scale=1.0):
    """

    .. todo::
        Document this function.

    :param cb:
    :param available:
    :param scale:
    :return:
    """
    set_habitat_scale(cb, scale)
    cb.set_param("Config_Name", StudySite.site + '_x_' + str(scale))
    nearest = lambda num, numlist: min(numlist, key=lambda x: abs(x - num))
    nearest_scale = scale if not available else nearest(scale, available)
    add_immune_init(cb, StudySite.site, [nearest_scale])
    return {'Config_Name': StudySite.site + '_x_' + str(scale),
            'habitat_scale': scale}