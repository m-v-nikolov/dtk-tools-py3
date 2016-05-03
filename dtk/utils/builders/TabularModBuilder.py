from simtools.ModBuilder import ModBuilder
from COMPS_Worker_Plugin import Builder_Plugin_Helper

import json, copy, os
from collections import OrderedDict, namedtuple

from COMPS_Worker_Plugin import Builder_Plugin_Helper
from COMPS_Worker_Plugin.Builder_JSON_Utilities import setParameter
from COMPS_Worker_Plugin.Builder_JSON_Utilities import findKeyPaths
from COMPS_Worker_Plugin.COMPS_Entities import *


# TODO: Match DEMOGRAPHICS KP parameters to individual files.  Make sure every KP entry can be found in at least one file
# TODO: Be more careful about using findKeyPaths.  Should precipitate from the above mapping of paramters to files

class TabularModBuilder(ModBuilder):
    def __init__(self, plugin_info_json, plugin_files_json, plugin_files_dir):
        '''
        plugin_info_json:
        plugin_files_json:
        plugin_files_dir:

        __plugininfo_filename = 'PluginInfo.json'
        __pluginfiles_path = 'PluginFiles'
        __pluginfilesmap_path = 'PluginFiles.json'
        __abortsemaphore_filename = 'AbortSemaphore.txt'
        __entity_path = 'Entities'
        __input_files_path = 'InputFiles'
        __input_files_files_path = os.path.join('InputFiles','Files')
        __input_files_destinations_path = os.path.join('InputFiles','Destinations')
        '''

        self.plugin_info_json = plugin_info_json
        self.plugin_files_json = plugin_files_json
        self.plugin_files_dir = plugin_files_dir

        # 1. Set switches based on what's in the ticket
        self.configure()

        # 2. Load templates
        self.load_templates()

        # 3. Set static parameters
        self.set_static_parameters()    # <-- handled by TabularConfigBuilder

        # 4 Product table by run number

        # 5. Set dynamic parameters
        self.set_dynamic_parameters()




        File = namedtuple('File', ['Name', 'Contents'])

        ph = Builder_Plugin_Helper()

        plugin_info = ph.GetPluginInfo()
        header = plugin_info['Dynamic_Parameters']['Header']

        # Maps from KP keyword to json path in file
        config_kp_dict = { }
        campaign_kp_dict = { }
        campaign_template = None
        demographics_kp_dict = { }
        demographics_filename_to_KPlist = { }
        demographics_templates = []

### BEGIN: CONFIGURE - interpret the ticket and determine what to do
        has_multiple_campaigns = 'CONFIG.Campaign_Filename' in header
        if has_multiple_campaigns:
            ph.Log('Multiple campaigns detected!')

        demographics_from_table = 'CONFIG.Demographics_Filenames' in header
        demographics_from_static = False
        if demographics_from_table:
            ph.Log('Demographics files will be selected on a per-simulation basis.')
        else:
            demographics_from_static = ('Static_Parameters' in plugin_info) and ('CONFIG.Demographics_Filenames' in plugin_info['Static_Parameters'])
            if demographics_from_static:
                ph.Log('Demographics files will be selected from static overlay.')

        all_parameters = (plugin_info['Static_Parameters'].keys() if 'Static_Parameters' in plugin_info else []) + plugin_info['Dynamic_Parameters']['Header']

        has_campaign_parameters = any( key.startswith('CAMPAIGN.') for key in all_parameters )
        if has_campaign_parameters:
            ph.Log('Variable campaign parameters detected.')

        has_demographics_parameters = any( key.startswith('DEMOGRAPHICS.') for key in all_parameters )
        if has_demographics_parameters:
            ph.Log('Variable demographics parameters detected.')

        has_explicit_run_numbers = 'CONFIG.Run_Number' in header
        if has_explicit_run_numbers:
            if 'Run_Number' in plugin_info['Dynamic_Parameters']:
                ph.Log('Explicit Run_Number column detected in Table!  Ignoring separate Run_Number array.')
            else:
                ph.Log('Explicit Run_Number column detected in Table!')
        elif 'Run_Number' not in plugin_info['Dynamic_Parameters']:
            raise RuntimeError('No Run_Number found (in Dynamic_Parameters or as an explicit column in Table/Header).')
### END: CONFIGURE

### BEGIN: LOAD - need file loader / manager class
        # load config
        with open(ph.GetPluginFilePath('CONFIG_TEMPLATE'), 'r') as file:
            config_filename = os.path.basename(file.name)
            ph.Log('Loading config')
            config_template = json.load(file, object_pairs_hook=OrderedDict)

        # load single campaign or read filenames of all CAMPAIGN_TEMPLATE filetypes to prep for multiple campaigns
        if not has_multiple_campaigns:
            campaign_path = ph.GetPluginFilePath('CAMPAIGN_TEMPLATE', required=False)

            if campaign_path is not None:
                campaign_filename = os.path.basename(campaign_path)
                with open(campaign_path, 'r') as file:
                    ph.Log('Loading campaign')
                    campaign_template = json.load(file, object_pairs_hook=OrderedDict)
            elif has_campaign_parameters:
                raise RuntimeError('No CAMPAIGN_TEMPLATE specified, but campaign parameter \'' + key + '\' found in WorkOrder')
        else:
            campaign_filename_col = header.index('CONFIG.Campaign_Filename')
            campaign_template_filemap = { os.path.basename(p) : p for p in ph.GetPluginFilePaths('CAMPAIGN_TEMPLATE') }
            campaign_template_map = { }

        # load single demographics file or read filenames of all DEMOGRAPHICS_TEMPLATE filetypes to prep for multiple demographics files
        if not demographics_from_table:
            demographics_paths = ph.GetPluginFilePaths('DEMOGRAPHICS_TEMPLATE', required=False)

            if demographics_paths:
                for demographics_path in demographics_paths:
                    demographics_filename = os.path.basename(demographics_path)
                    with open(demographics_path, 'r') as file:
                        ph.Log('Loading demographics')
                        demographics_contents = json.load(file, object_pairs_hook=OrderedDict)
                        demographics_templates.append( File(Name=demographics_filename, Contents=demographics_contents) )
            elif has_demographics_parameters:
                raise RuntimeError('No DEMOGRAHPICS_TEMPLATE specified, but variable demographics parameter \'' + key + '\' found in WorkOrder')
        else:
            demographics_filename_col = header.index('CONFIG.Demographics_Filenames')
            # demographics_template_filemap: filename --> path to file
            demographics_template_filemap = { os.path.basename(p) : p for p in ph.GetPluginFilePaths('DEMOGRAPHICS_TEMPLATE', required=has_demographics_parameters) }
            demographics_template_map = { }

        # get list of any additional input-files to be copied to the sim working dir
        additional_input_file_paths = ph.GetPluginFilePaths('ADDITIONAL_INPUT_FILE', required=False)
### END: LOAD

### BEGIN: SET STATIC PARAMETERS - should live in the "config builder"
        # set static parameters (only for config if multiple campaigns)
        if 'Static_Parameters' in plugin_info:
            for key, val in plugin_info['Static_Parameters'].iteritems():
                if key.startswith('CONFIG.'):
                    ph.Log('Setting static config parameter: ' + key[ len('CONFIG.') : ] + ' - ' + str(val))
                    setParameter(config_template['parameters'], key[ len('CONFIG.') : ], val, config_kp_dict)
                elif key.startswith('CAMPAIGN.'):
                    if not has_multiple_campaigns:
                        ph.Log('Setting static campaign parameter: ' + key[ len('CAMPAIGN.') : ] + ' - ' + str(val))
                        setParameter(campaign_template['Events'], key[ len('CAMPAIGN.') : ], val, campaign_kp_dict)
                elif key.startswith('DEMOGRAPHICS.'):
                    if not demographics_from_table:
                        subkey = key[ len('DEMOGRAPHICS.') : ]
                        ph.Log('Setting static demographics parameter: ' + subkey + ' - ' + str(val))
                        for demographics_template in demographics_templates:
                            if demographics_template.Name not in demographics_filename_to_KPlist:
                                demographics_filename_to_KPlist[demographics_template.Name] = {}

                            if subkey not in demographics_filename_to_KPlist[demographics_template.Name]:
                                # Look for the key in the current demographics file.  Map to boolean.
                                demographics_filename_to_KPlist[demographics_template.Name][subkey] = len(findKeyPaths(demographics_template.Contents, subkey))>0

                            if demographics_template.Name not in demographics_kp_dict:
                                demographics_kp_dict[demographics_template.Name] = { }

                            if demographics_filename_to_KPlist[demographics_template.Name][subkey]:
                                ph.Log('Setting static demographics parameter: ' + subkey + ' = ' + str(val))
                                setParameter(demographics_template.Contents, subkey, val, demographics_kp_dict[demographics_template.Name])
                else:
                    raise RuntimeError('Only CONFIG, CAMPAIGN, and DEMOGRAPHICS prefixes are allowed in Static_Parameters')
### END: SET STATIC PARAMETERS

        if not ph.ContinueProcessing():
            exit(0)

### BEGIN: CREATE_EXPERIMENT - should not need to do this in simtools
        # create the base experiment
        exp = Experiment()
        exp['Tags'] = {
            'nPts': len(plugin_info['Dynamic_Parameters']['Table']),
            'nRep': 1 if has_explicit_run_numbers else len(plugin_info['Dynamic_Parameters']['Run_Number'])
        }
        ph.CreateExperiment(exp)
### END: CREATE_EXPERIMENT

### BEGIN: SET DYNAMIC PARAMETERS

        ####################################################################################################
        # Loop over rows (a.k.a. TestPointIndex) in 'Table' from the plugin info section of the work-order #
        ####################################################################################################
        for tpi in range(len(plugin_info['Dynamic_Parameters']['Table'])):
### Each one of these is a entry in the mod_generator

            config_current = copy.deepcopy(config_template) # <-- done automatically

            rowdata = plugin_info['Dynamic_Parameters']['Table'][tpi]
            tags = { 'TestPointIndex': tpi + 1 }

            # if multiple campaigns, then we need to load the campaign for this row and set the static parameters
            if has_multiple_campaigns:
                if rowdata[campaign_filename_col] in campaign_template_map:
                    campaign_current = copy.deepcopy(campaign_template_map[rowdata[campaign_filename_col]])
                else:
                    with open(campaign_template_filemap[rowdata[campaign_filename_col]], 'r') as file:
                        campaign_filename = rowdata[campaign_filename_col]
                        ph.Log('Loading campaign ' + campaign_filename)
                        campaign_current = json.load(file, object_pairs_hook=OrderedDict)

                    campaign_kp_dict[rowdata[campaign_filename_col]] = { }

                    if 'Static_Parameters' in plugin_info:
                        for key, val in plugin_info['Static_Parameters'].iteritems():
                            if key.startswith('CAMPAIGN.'):
                                ph.Log('Setting static campaign parameter: ' + key[ len('CAMPAIGN.') : ] + ' - ' + str(val))
                                setParameter(campaign_current['Events'], key[ len('CAMPAIGN.') : ], val, campaign_kp_dict[rowdata[campaign_filename_col]])

                    campaign_template_map[rowdata[campaign_filename_col]] = copy.deepcopy(campaign_current)
            else:
                campaign_current = copy.deepcopy(campaign_template)


            # If multiple demographics, then we need to load the demographics for this row and set the static parameters
            demographics_list = []
            if demographics_from_table:
                for demographics_filename in rowdata[demographics_filename_col]:
                    if demographics_filename in demographics_template_map:
                        # We've already done the static param overlay, just make a copy
                        demographics_current = copy.deepcopy(demographics_template_map[demographics_filename])
                        demographics_list.append(demographics_current)
                    elif demographics_filename in demographics_template_filemap:
                        # New demographics file, need to do static overlay
                        with open(demographics_template_filemap[demographics_filename], 'r') as file:
                            ph.Log('Loading demographics ' + demographics_filename)
                            demographics_contents = json.load(file, object_pairs_hook=OrderedDict)
                            demographics_current = File(Name=demographics_filename, Contents=demographics_contents)

                        if demographics_filename not in demographics_kp_dict:
                            demographics_kp_dict[demographics_filename] = { }

                        if 'Static_Parameters' in plugin_info:
                            for key, val in plugin_info['Static_Parameters'].iteritems():
                                if key.startswith('DEMOGRAPHICS.'):
                                    subkey = key[ len('DEMOGRAPHICS.') : ]
                                    if demographics_filename not in demographics_filename_to_KPlist:
                                        demographics_filename_to_KPlist[demographics_filename] = {}

                                    if subkey not in demographics_filename_to_KPlist[demographics_filename]:
                                        # Look for the key in the current demographics file
                                        demographics_filename_to_KPlist[demographics_filename][subkey] = len( findKeyPaths(demographics_current.Contents, subkey) )>0

                                    if demographics_filename_to_KPlist[demographics_filename][subkey]:
                                        ph.Log('Setting static demographics parameter: ' + subkey + ' = ' + str(val))
                                        setParameter(demographics_current.Contents, key[ len('DEMOGRAPHICS.') : ], val, demographics_kp_dict[demographics_filename])

                        demographics_template_map[demographics_filename] = copy.deepcopy(demographics_current)
                        demographics_list.append( copy.deepcopy(demographics_current) )
            else:
                if demographics_from_static:
                    demographics_filenames =  plugin_info['Static_Parameters']['CONFIG.Demographics_Filenames']
                elif demographics_templates:
                    demographics_filenames = config_current['parameters']['Demographics_Filenames']

                for demographics_template in demographics_templates:
                    if demographics_template.Name in demographics_filenames:
                        demographics_kp_dict[demographics_template.Name] = {}
                        demographics_list.append( copy.deepcopy(demographics_template) )

            if demographics_list:
                ph.Log( 'Demographics files used from template: ' + str( [d.Name for d in demographics_list] ) )

            # set dynamic parameters
            for col in range(len(header)):
### Each one of these is a mod_fn
                if header[col].startswith('CONFIG.'):
                    ph.Log('Setting dynamic config parameter: ' + header[col][ len('CONFIG.') : ] + ' - ' + str(rowdata[col]))
                    setParameter(config_current['parameters'], header[col][ len('CONFIG.') : ], rowdata[col], config_kp_dict)
                    tags[header[col][ len('CONFIG.') : ]] = json.dumps(rowdata[col]) if isinstance(rowdata[col], list) or isinstance(rowdata[col], dict) else rowdata[col]
                elif header[col].startswith('CAMPAIGN.'):
                    ph.Log('Setting dynamic campaign parameter: ' + header[col][ len('CAMPAIGN.') : ] + ' - ' + str(rowdata[col]))
                    if has_multiple_campaigns:
                        setParameter(campaign_current['Events'], header[col][ len('CAMPAIGN.') : ], rowdata[col], campaign_kp_dict[rowdata[campaign_filename_col]])
                    else:
                        setParameter(campaign_current['Events'], header[col][ len('CAMPAIGN.') : ], rowdata[col], campaign_kp_dict)
                    tags[header[col][ len('CAMPAIGN.') : ]] = json.dumps(rowdata[col]) if isinstance(rowdata[col], list) or isinstance(rowdata[col], dict) else rowdata[col]
                elif header[col].startswith('DEMOGRAPHICS.'):
                    subkey = header[col][ len('DEMOGRAPHICS.') : ]

                    for demographics_current in demographics_list:
                        if demographics_current.Name not in demographics_filename_to_KPlist:
                            demographics_filename_to_KPlist[demographics_current.Name] = {}

                        if subkey not in demographics_filename_to_KPlist[demographics_current.Name]:
                            demographics_filename_to_KPlist[demographics_current.Name][subkey] = len( findKeyPaths(demographics_current.Contents, subkey) )>0

                        if demographics_filename_to_KPlist[demographics_current.Name][subkey]:
                            ph.Log('Setting dynamic demographics parameter: ' + subkey + ' = ' + str(rowdata[col]) + ' in file ' + demographics_current.Name )
                            setParameter(demographics_current.Contents, subkey, rowdata[col], demographics_kp_dict[demographics_current.Name])

                    tags[subkey] = json.dumps(rowdata[col]) if isinstance(rowdata[col], list) or isinstance(rowdata[col], dict) else rowdata[col]
                else:
                    ph.Log('No matching prefixes found for parameter \'' + header[col] + '\'; creating tag only')
                    tags[header[col]] = json.dumps(rowdata[col]) if isinstance(rowdata[col], list) or isinstance(rowdata[col], dict) else rowdata[col]
                    # raise RuntimeError('Only CONFIG, CAMPAIGN, and DEMOGRAPHICS prefixes are allowed in Dynamic_Parameters')

            if campaign_current is not None:
                campaign_str = json.dumps(campaign_current, indent=4)

            demographics_str = {}
            for demographics_current in demographics_list:
                demographics_str[demographics_current.Name] = json.dumps(demographics_current.Contents, indent=4)

            # loop over Run_Number (a.k.a. Replicate)
### Need product space over run number for simtools

### Mod functions will be applied to files directly, no need to stack sf
            for rep in range(1 if has_explicit_run_numbers else len(plugin_info['Dynamic_Parameters']['Run_Number'])):
                if not has_explicit_run_numbers:
                    config_current['parameters']['Run_Number'] = plugin_info['Dynamic_Parameters']['Run_Number'][rep]
                config_str = json.dumps(config_current, indent=4)
                tags['Replicate'] = rep + 1
                tags['Run_Number'] = config_current['parameters']['Run_Number']

                # set the various bits of metadata and create the Simulation
                simfiles = []

                sf = SimulationFile()
                sf['FileName'] = config_filename
                sf['Description'] = 'basic builder-generated config'
                sf['Contents'] = config_str
                simfiles.append(sf)

                if campaign_current is not None:
                    sf2 = SimulationFile()
                    sf2['FileName'] = campaign_filename
                    sf2['Description'] = 'builder-generated campaign'
                    sf2['Contents'] = campaign_str
                    simfiles.append(sf2)

                for demographics_current in demographics_list:
                    if demographics_current is not None:
                        sf2 = SimulationFile()
                        sf2['FileName'] = demographics_current.Name
                        sf2['Description'] = 'builder-generated demographics'
                        sf2['Contents'] = demographics_str[demographics_current.Name]
                        simfiles.append(sf2)

                for p in additional_input_file_paths:
                    sf3 = SimulationFile()
                    sf3['FileName'] = os.path.basename(p)
                    sf3['Description'] = 'additional input file'
                    with open(p, 'r') as file:
                        sf3['Contents'] = file.read()
                    simfiles.append(sf3)

                sim = Simulation()
                sim['Tags'] = tags

                if not ph.ContinueProcessing():
                    exit(0)

### Handled by simtools
                ph.Log('Creating simulation {' + str(tpi + 1) + ',' + str(rep + 1) + '}')
                ph.CreateSimulation( sim, simfiles )

### END: SET DYNAMIC PARAMETERS
