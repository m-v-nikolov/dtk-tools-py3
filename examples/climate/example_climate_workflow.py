# Node 1001: mapped to 27.6, -17.05, 2008 climate
# All other nodes: temperature as in attached CSV, humidity and rainfall as in 2008 climate at 28.0, -16.5
# Slim climate is fine.
import csv
import json
import os
import time
from collections import OrderedDict

import struct

from dtk.tools.climate.ClimateFileCreator import ClimateFileCreator
from dtk.tools.climate.WeatherNode import WeatherNode
from dtk.tools.demographics.DemographicsFile import DemographicsFile
from dtk.tools.demographics.node import Node
from simtools.COMPSAccess.WorkOrderGenerator import WorkOrderGenerator
from simtools.OutputParser import SimulationOutputParser
from simtools.SetupParser import SetupParser


# Create the 2 nodes we need to pull weather for
nodes = [
    Node(lon=27.6, lat=-17.05, name='Node 1001', pop=1000),
    Node(lon=28, lat=-16.5, name='Others', pop=1000)
]

# Create the file
dg = DemographicsFile(nodes)
dg.generate_file('climate_demog.json')

# Create the workorder
wo = WorkOrderGenerator(demographics_file_path='climate_demog.json',wo_output_path='output',  project_info='IDM-Zambia', start_year='2008', num_years='1', resolution='0')

# Get the weather from COMPS
sp = SetupParser('HPC')
from COMPS import Client
from COMPS.Data import QueryCriteria, AssetType
from COMPS.Data import WorkItem, WorkItemFile, WorkItem__WorkerOrPluginKey as WorkerKey
from java.util import HashMap, ArrayList

workerkey = WorkerKey('InputDataWorker', '1.0.0.0_RELEASE')
wi = WorkItem('dtk-tools InputDataWorker WorkItem', sp.get('environment'), workerkey)
tagmap = HashMap()
tagmap.put('dtk-tools', None)
tagmap.put('WorkItem type', 'InputDataWorker dtk-tools')
wi.SetTags(tagmap)

wi.AddWorkOrder(json.dumps(wo.wo_2_dict()))
wi.AddFile(WorkItemFile('climate_demog.json', 'Demographics', ''),json.dumps(dg.content))
wi.Save()
wi.Commission()

while (wi.getState().toString() not in ['Succeeded', 'Failed', 'Canceled']):
    print "Waiting for work order to finish..."
    time.sleep(1)
    wi.Refresh()

print "Successfully generated"

wi.Refresh(QueryCriteria().select_children('files'))
wifiles = wi.getFiles().toArray()
wifilenames = [wif.getFileName() for wif in wifiles if wif.getFileType() == 'Output']
if len(wifilenames) > 0:
    print 'Found output files: ' + str(wifilenames)
    print 'Downloading now'

    javalist = ArrayList()
    for f in wifilenames:
        javalist.add(f)

    assets = wi.RetrieveAssets(AssetType.Linked,  javalist)

    for i in range(len(wifilenames)):
        with open(os.path.join('intermediate/climate', wifilenames[i]), 'wb') as outfile:
            outfile.write(assets.get(i).tostring())


# We now have the intermediate weather -> Create the list of nodes
# Extract the nodes from the demog

def extract_data_from_bin(node, binary_file):
    meta = json.load(open(binary_file+'.json','rb'))
    tsteps = meta['Metadata']['DatavalueCount']
    offsets = meta['NodeOffsets']
    offsets_nodes = OrderedDict()
    i=0
    while i <len(offsets):
        nodeid = int(offsets[i:i+8],16)
        offset = int(offsets[i+9:i+16], 16)
        offsets_nodes[nodeid] = offset
        i+=16

    series = []
    with open(binary_file, 'rb') as bin_file:
        bin_file.seek(offsets_nodes[node.id])

        # Read the data
        for i in range(tsteps):
            series.append(struct.unpack('f', bin_file.read(4))[0])
    return series

# Load or base climate nodes
demog = json.load(open('climate_demog.json','rb'))
climate_nodes = {}
for node in demog['Nodes']:
    n = WeatherNode()
    n.id = node['NodeID']

    n.air_temperature = extract_data_from_bin(n, 'intermediate/climate/Zambia_30arcsec_air_temperature_daily.bin')
    n.land_temperature = extract_data_from_bin(n, 'intermediate/climate/Zambia_30arcsec_air_temperature_daily.bin')
    n.rainfall = extract_data_from_bin(n, 'intermediate/climate/Zambia_30arcsec_rainfall_daily.bin')
    n.humidity = extract_data_from_bin(n, 'intermediate/climate/Zambia_30arcsec_relative_humidity_daily.bin')

    climate_nodes[node['NodeAttributes']['FacilityName']] = n

# Load Jaline's nodes from the demographics file
demog = json.load(open('inputs/Bbondo_households_demographics_CBfilled_noworkvector.json'))
nodes = []

# Get the temperature from CSV
temperature_csv = list()
for temp in csv.DictReader(open('inputs/one_year_series_add_one_degree.csv')):
    temperature_csv.append(float(temp['temperature']))

for node in demog['Nodes']:
    n = WeatherNode()
    n.id = node['NodeID']
    # Fill the temp/humid/rain according to directions
    if n.id == 1001:
        n.air_temperature = climate_nodes['Node 1001'].air_temperature
        n.land_temperature = climate_nodes['Node 1001'].land_temperature
        n.humidity = climate_nodes['Node 1001'].humidity
        n.rainfall = climate_nodes['Node 1001'].rainfall
    else:
        n.humidity = climate_nodes['Others'].humidity
        n.rainfall = climate_nodes['Others'].rainfall
        n.air_temperature = temperature_csv
        n.land_temperature = temperature_csv

    nodes.append(n)

# Create our files from the nodes
cfc = ClimateFileCreator(nodes,'Bbondo_households_CBfilled_noworkvector','daily','2008-2008','Household-Scenario-Small', True)
current_dir = os.path.dirname(os.path.realpath(__file__))
cfc.generate_climate_files(os.path.join(current_dir,'output'))