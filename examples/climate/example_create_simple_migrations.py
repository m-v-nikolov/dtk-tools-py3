import os

from dtk.tools.demographics.DemographicsFile import DemographicsFile
from dtk.tools.migration.MigrationFile import MigrationFile

# In this example we will demonstrate how to create simple migrations
# All you need as an input is a demographics file with more than one node

# Load the demographics file
demog = DemographicsFile.from_file('inputs/demographics_for_migration.json')

# Get our nodes
base = demog.get_node('base')
extra_1 = demog.get_node('extra_1')
extra_2 = demog.get_node('extra_2')

# Create some local migrations
local_migrations = {
    base: {
        extra_1: .01
    },
    extra_2: {
        base: .02,
        extra_1: .03
    }
}

# Create the output path
output_path = 'outputs_migration'
if not os.path.exists(output_path): os.makedirs(output_path)

# Generate the migration file
mig = MigrationFile(demog.idref, local_migrations)
mig.generate_file(os.path.join(output_path, 'local_migrations.bin'))
