# Node 1001: mapped to 27.6, -17.05, 2008 climate
# All other nodes: temperature as in attached CSV, humidity and rainfall as in 2008 climate at 28.0, -16.5
import csv
import json
import os

from dtk.tools.climate.BinaryFilesHelpers import extract_data_from_climate_bin_for_node
from dtk.tools.climate.ClimateFileCreator import ClimateFileCreator
from dtk.tools.climate.ClimateGenerator import ClimateGenerator
from dtk.tools.climate.WeatherNode import WeatherNode
from dtk.tools.demographics.DemographicsFile import DemographicsFile
from dtk.tools.demographics.Node import Node
from simtools.SetupParser import SetupParser

# Set up the paths
current_dir = os.path.dirname(os.path.realpath(__file__))
output_path = os.path.join(current_dir, 'output')
intermediate_dir = os.path.join(current_dir, 'intermediate', 'climate')

# Make sure we have directory created
if not os.path.exists(intermediate_dir): os.makedirs(intermediate_dir)
if not os.path.exists(output_path): os.makedirs(output_path)

# Get a setup
SetupParser.init('HPC')

# Create the 2 nodes we need to pull weather for
nodes = [
    Node(lon=27.6, lat=-17.05, name='Node 1001', pop=1000),
    Node(lon=28, lat=-16.5, name='Others', pop=1000)
]

# Create the file
dg = DemographicsFile(nodes)
climate_demog = os.path.join(intermediate_dir, 'climate_demog.json')
dg.generate_file(climate_demog)

cg = ClimateGenerator(demographics_file_path=climate_demog,
                      work_order_path=os.path.join(intermediate_dir, 'wo.json'),
                      climate_files_output_path=intermediate_dir,
                      climate_project='IDM-Zambia',
                      start_year='2008', num_years='1', resolution='0', idRef="Gridded world grump2.5arcmin")

rain_fname, humidity_fname, temperature_fname = cg.generate_climate_files()

# We now have the intermediate weather -> Create the list of nodes
# Extract the nodes from the demog
# Load the base climate nodes
demog = json.load(open(climate_demog, 'rb'))
climate_nodes = {}
for node in demog['Nodes']:
    n = WeatherNode()
    n.id = node['NodeID']

    n.air_temperature = extract_data_from_climate_bin_for_node(n, os.path.join(intermediate_dir, temperature_fname))
    n.land_temperature = extract_data_from_climate_bin_for_node(n, os.path.join(intermediate_dir, temperature_fname))
    n.rainfall = extract_data_from_climate_bin_for_node(n, os.path.join(intermediate_dir, rain_fname))
    n.humidity = extract_data_from_climate_bin_for_node(n, os.path.join(intermediate_dir, humidity_fname))

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
cfc = ClimateFileCreator(nodes, 'Bbondo_households_CBfilled_noworkvector', 'daily', '2008-2008',
                         'Household-Scenario-Small')
cfc.generate_climate_files(output_path)

print "--------------------------------------"
print "Climate generated in %s" % output_path
