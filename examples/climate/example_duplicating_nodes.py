import json
import os

from dtk.tools.climate.BinaryFilesHelpers import extract_data_from_climate_bin_for_node
from dtk.tools.climate.ClimateFileCreator import ClimateFileCreator
from dtk.tools.climate.WeatherNode import WeatherNode

# In this example we have a one node weather and demographics
# We are going to use this one node to actually create additional nodes
# With the same weather and set up some migrations between them

# First lets define which node will be our base node
# For now we are using the only node present in the demographics file (inputs/Santander/IDM-Colombia_Santander_shape_nodes_demographics.json)
from dtk.tools.demographics.DemographicsFile import DemographicsFile

input_path = os.path.join('inputs', 'Santander')
base_demog_path = os.path.join(input_path, 'IDM-Colombia_Santander_shape_nodes_demographics.json')
base_demog = json.load(open(base_demog_path,'rb'))
base_node_data = base_demog['Nodes'][0]['NodeAttributes']
base_node_id = base_demog['Nodes'][0]['NodeID']

# Create the base_node object with the info found in the Demographics
# Because sometimes, the ids of the demographics are not following the normal way to generate
# We are manually specifying a forced_id to make sure we are consistent with the climate files
base_node = WeatherNode(name='base', lat=base_node_data['Latitude'], lon=base_node_data['Longitude'], pop=base_node_data['InitialPopulation'], forced_id=base_node_id)

# Now lets create the nodes that we want to use
# For this example we just move slightly the 2 extra nodes
nodes = [
    base_node,
    WeatherNode(name='extra_1', lat=base_node.lat-0.05, lon=base_node.lon-0.05, pop=1000),
    WeatherNode(name='extra_2', lat=base_node.lat+0.05, lon=base_node.lon+0.05, pop=200)
]

# Be careful not to move the extra node not too close as the node_ids only support a certain resolution
# A way to check if the resolution was too small is to ensure we have unique node_ids
# The following line compare the lengths of the nodes list with the length of unique ids
assert (len(nodes) == len(set([n.id for n in nodes])))

# Now we need to get the weather out of the current binary files
# There is a helper function called extract_data_from_climate_bin allowing to extra from climate binaries files for a given node
# We want to retrieve the data for the base node
temperature_base = extract_data_from_climate_bin_for_node(base_node, os.path.join(input_path,'Colombia_Santander_2.5arcmin_air_temperature_daily.bin'))
rainfall_base = extract_data_from_climate_bin_for_node(base_node, os.path.join(input_path,'Colombia_Santander_2.5arcmin_rainfall_daily.bin'))
humidity_base = extract_data_from_climate_bin_for_node(base_node, os.path.join(input_path,'Colombia_Santander_2.5arcmin_relative_humidity_daily.bin'))

# Now we have the climate data from the base node add it to all our nodes
for n in nodes:
    n.air_temperature = temperature_base
    n.rainfall = rainfall_base
    n.humidity = humidity_base

# All our nodes have values, create the output files
# For that we are going to open one of the metadata file in order to keep everything consistant
meta = json.load(open(os.path.join(input_path, 'Colombia_Santander_2.5arcmin_air_temperature_daily.bin.json'),'rb'))['Metadata']

output_path = 'outputs_Santander'
if not os.path.exists(output_path): os.makedirs(output_path)

cfc = ClimateFileCreator(nodes,
                         prefix='Colombia_Santander_2.5arcmin',
                         suffix='daily',
                         original_data_years=meta['OriginalDataYears'],
                         idref=meta['IdReference'])

cfc.generate_climate_files(output_path)

# Create the demographics file
dg = DemographicsFile(nodes, base_file=base_demog_path)
dg.generate_file(os.path.join(output_path, 'demographics.json'))

# The files should be created -> display a message
print "The output files have been created in the %s folder!" % output_path


