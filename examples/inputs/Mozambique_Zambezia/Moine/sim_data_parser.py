import pandas as pd
import json
import numpy as np

with open("InsetChart.json", "r") as ic:
	data = json.load(ic)
	
data = data["Channels"]["New Clinical Cases"]["Data"]

data = np.array(data[2*365:])

# aggregate by month (assuming we have 24 months of data, which is "not the smartest..")

cc_split_monthly = np.array_split(data, 24)

cc_data = {}
for i, cc_monthly in enumerate(cc_split_monthly):
	cc_data[i] = np.sum(cc_monthly)

print (cc_data)
	
df = pd.DataFrame.from_dict(cc_data, orient="index")

df.index.name = 'month'
df['month']=df.index
df = df.reset_index(drop=True)

df.columns = ['cc', 'month']

sim_data = df.rename(columns={'cc': 'Counts'})
sim_data['Channel'] = ['Clinical_Cases'] * len(sim_data)

sim_data = sim_data.sort_values(['Channel', 'month'])
sim_data = sim_data.set_index(['Channel', 'month'])

print (sim_data)