# Node 1001: mapped to 27.6, -17.05, 2008 climate
# All other nodes: temperature as in attached CSV, humidity and rainfall as in 2008 climate at 28.0, -16.5
# Slim climate is fine.
import csv
import json
import os
import time

from COMPS.Data import QueryCriteria, AssetType
from COMPS.Data import WorkItem, WorkItemFile
from COMPS.Data.WorkItem import WorkerOrPluginKey, WorkItemState

from dtk.tools.climate.BinaryFilesHelpers import extract_data_from_climate_bin_for_node
from dtk.tools.climate.ClimateFileCreator import ClimateFileCreator
from dtk.tools.climate.WeatherNode import WeatherNode
from dtk.tools.demographics.DemographicsFile import DemographicsFile
from dtk.tools.demographics.node import Node
from simtools.COMPSAccess.WorkOrderGenerator import WorkOrderGenerator
from simtools.SetupParser import SetupParser

# Set up the paths
current_dir = os.path.dirname(os.path.realpath(__file__))
output_path = os.path.join(current_dir,'output')
internediate_dir = os.path.join(current_dir, 'intermediate','climate')

# Make sure we have directory created
if not os.path.exists(internediate_dir): os.makedirs(internediate_dir)
if not os.path.exists(output_path): os.makedirs(output_path)

# Get a setup
sp = SetupParser('HPC')

# Create the 2 nodes we need to pull weather for
nodes = [
    Node(lon=27.6, lat=-17.05, name='Node 1001', pop=1000),
    Node(lon=28, lat=-16.5, name='Others', pop=1000)
]

# Create the file
dg = DemographicsFile(nodes)
dg.generate_file('climate_demog.json')

# Create the workorder
wo = WorkOrderGenerator(demographics_file_path='climate_demog.json', wo_output_path='output',  project_info='IDM-Zambia', start_year='2008', num_years='1', resolution='0')

# Get the weather from COMPS
workerkey = WorkerOrPluginKey(name='InputDataWorker', version='1.0.0.0_RELEASE')

wi = WorkItem('dtk-tools InputDataWorker WorkItem', workerkey, sp.get('environment'))
wi.set_tags({'dtk-tools':None, 'WorkItem type':'InputDataWorker dtk-tools'})
wi.add_work_order(data=json.dumps(wo.wo_2_dict()))
wi.add_file(WorkItemFile('climate_demog.json', 'Demographics', ''), data=json.dumps(dg.content))
wi.save()
wi.commission()

while wi.state not in [WorkItemState.Succeeded, WorkItemState.Failed, WorkItemState.Canceled]:
    print "Waiting for work order to finish... (Current state = %s)" % wi.state
    time.sleep(3)
    wi.refresh()

print "Successfully generated"

# Get the files out of the workorder
wi.refresh(QueryCriteria().select_children('files'))
wifilenames = [wif.file_name for wif in wi.files if wif.file_type == 'Output']

if len(wifilenames) > 0:
    print 'Found output files: ' + str('\n'.join(wifilenames))
    print 'Downloading now'

    assets = wi.retrieve_assets(AssetType.Linked, wifilenames)

    for i in range(len(wifilenames)):
        with open(os.path.join(internediate_dir, wifilenames[i]), 'wb') as outfile:
            outfile.write(assets[i])


# We now have the intermediate weather -> Create the list of nodes
# Extract the nodes from the demog
# Load or base climate nodes
demog = json.load(open('climate_demog.json', 'rb'))
climate_nodes = {}
for node in demog['Nodes']:
    n = WeatherNode()
    n.id = node['NodeID']

    n.air_temperature = extract_data_from_climate_bin_for_node(n, 'intermediate/climate/Zambia_30arcsec_air_temperature_daily.bin')
    n.land_temperature = extract_data_from_climate_bin_for_node(n, 'intermediate/climate/Zambia_30arcsec_air_temperature_daily.bin')
    n.rainfall = extract_data_from_climate_bin_for_node(n, 'intermediate/climate/Zambia_30arcsec_rainfall_daily.bin')
    n.humidity = extract_data_from_climate_bin_for_node(n, 'intermediate/climate/Zambia_30arcsec_relative_humidity_daily.bin')

    climate_nodes[node['NodeAttributes']['FacilityName']] = n

# Load nodes from the demographics file
demog = json.load(open('inputs/Bbondo_households_demographics_CBfilled_noworkvector.json'))
nodes = []

# Get the temperature from CSV
temperature_csv = list()
for temp in csv.DictReader(open('inputs/temperature_one_year_series.csv')):
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
cfc = ClimateFileCreator(nodes,'Bbondo_households_CBfilled_noworkvector','daily','2008-2008','Household-Scenario-Small')
cfc.generate_climate_files(output_path)

print "--------------------------------------"
print "Climate generated in %s" % output_path