import os
import json
import getpass
import datetime

from simtools.OutputParser import CompsDTKOutputParser

from simtools.SetupParser import SetupParser
from dtk.tools.demographics import createimmunelayer as imm
from dtk.vector.study_sites import geography_from_site
from dtk.generic.geography import get_geography_parameter

from COMPS import Client
Client.Login(SetupParser().get('server_endpoint'))

with open("simulations/burnin_b63f325d-d9df-e511-93fb-f0921c16b9e3.json") as metadata_file:
    md = json.loads(metadata_file.read())

sim_map = CompsDTKOutputParser.createSimDirectoryMap(md['exp_id'])

for simId, sim in md['sims'].items():
    site = sim['_site_']
    geography = geography_from_site(site)
    demog_name = get_geography_parameter(geography, 'Demographics_Filenames')[0].replace('compiled.', '')

    immunity_report_path = os.path.join(sim_map[simId], 'output', 'MalariaImmunityReport_FinalYearAverage.json')

    with open(os.path.join(SetupParser().get('LOCAL', 'input_root'), demog_name)) as f:
        j = json.loads(f.read())

    metadata = j['Metadata']
    metadata.update({'Author': getpass.getuser(),
                     'DateCreated': datetime.datetime.now().strftime('%a %b %d %X %Y'),
                     'Tool': os.path.basename(__file__)})

    imm.immune_init_from_custom_output({"Metadata": metadata,
                                        "Nodes": [{"NodeID": n['NodeID']} for n in j['Nodes']]}, 
                                        immunity_report_path, 
                                        ConfigName='x_%s' % sim['x_Temporary_Larval_Habitat'], 
                                        BaseName=demog_name,
                                        site='Sinamalima',
                                        doWrite=True,
                                        doCompile=False)
