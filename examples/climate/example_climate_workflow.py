# Node 1001: mapped to 27.6, -17.05, 2008 climate
# All other nodes: temperature as in attached CSV, humidity and rainfall as in 2008 climate at 28.0, -16.5
import csv
import os

from dtk.tools.climate.ClimateFileCreator import ClimateFileCreator
from dtk.tools.climate.ClimateGenerator import ClimateGenerator
from dtk.tools.climate.WeatherNode import WeatherNode
from dtk.tools.demographics.DemographicsFile import DemographicsFile
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
node_1001 = WeatherNode(lon=27.6, lat=-17.05, name='Node 1001', pop=1000)
node_others = WeatherNode(lon=28, lat=-16.5, name='Others', pop=1000)
nodes = [node_1001, node_others]

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

# Load the data from the files
node_1001.data_from_files(air_temperature=os.path.join(intermediate_dir, temperature_fname),
                          humidity=os.path.join(intermediate_dir, humidity_fname),
                          rainfall=os.path.join(intermediate_dir, rain_fname))

node_others.data_from_files(air_temperature=os.path.join(intermediate_dir, temperature_fname),
                            humidity=os.path.join(intermediate_dir, humidity_fname),
                            rainfall=os.path.join(intermediate_dir, rain_fname))

# Get the temperature from CSV
temperature_csv = list()
for temp in csv.DictReader(open('inputs/temperature_one_year_series.csv')):
    temperature_csv.append(float(temp['temperature']))

# Load the target demographics
target_demog = DemographicsFile.from_file("inputs/Bbondo_households_demographics_CBfilled_noworkvector.json")
nodes = []
for node in target_demog.nodes.values():
    # Fill the temp/humid/rain according to directions
    if node.id == 1001:
        node.air_temperature = node_1001.air_temperature
        node.land_temperature = node_1001.air_temperature
        node.humidity = node_1001.humidity
        node.rainfall = node_1001.rainfall
    else:
        node.humidity = node_others.humidity
        node.rainfall = node_others.rainfall
        node.air_temperature = node.land_temperature = temperature_csv

    nodes.append(node)

# Create our files from the nodes
cfc = ClimateFileCreator(nodes=nodes,
                         prefix='Bbondo_households_CBfilled_noworkvector', suffix='daily', original_data_years='2008',
                         idref='Household-Scenario-Small')

cfc.generate_climate_files(output_path)
print "--------------------------------------"
print "Climate generated in %s" % output_path
