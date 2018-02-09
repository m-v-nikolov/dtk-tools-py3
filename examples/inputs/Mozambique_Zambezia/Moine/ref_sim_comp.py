import pandas as pd
import json
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import datetime as dt


comparison_num_months = 24
comparison_start_date = dt.date(2014, 1, 1)
comparison_sim_start_day = 10*365

def set_datetime(x):
	m = x['month']
	if m <= 12:
		x['month'] = comparison_start_date.replace(month = m)
	else:
		x['month'] = comparison_start_date.replace(month = (m-1)%12 + 1, year = 2014 + int(m/12))
	return x['month']
	
	

with open("InsetChart_best_fit.json", "r") as bf:
	data = json.load(bf)
	
data_sim = data["Channels"]["New Clinical Cases"]["Data"]

data_sim = np.array(data_sim[comparison_sim_start_day:])

# aggregate by month (assuming we have 24 months of data, which is "not the smartest..")

cc_split_monthly = np.array_split(data_sim, comparison_num_months)

cc_data_sim = np.zeros(comparison_num_months)
for i, cc_monthly in enumerate(cc_split_monthly):
	cc_data_sim[i] = np.sum(cc_monthly)

	
df = pd.read_csv("cc_ref_data.csv")

df['Simulation'] = cc_data_sim

df = df.rename(columns = {"cc":"Reference"})

df = df.set_index("month")
df = df.stack()
df = df.reset_index()
df = df.rename(columns = {'level_1': 'type', 0:'Clinical cases'})
df["Date"] = df.apply(set_datetime, axis = 1)

print(df)

ax = plt.subplot()

g = sns.barplot(x = "Date", y = 'Clinical cases', data = df, hue = "type", ax = ax)

g.set_xticklabels(g.get_xticklabels(), rotation=45)

plt.setp(ax.get_legend().get_texts(), fontsize='19') 
plt.setp(ax.get_legend().get_title(), fontsize='23')

ax.tick_params(axis='x', which='major', labelsize=16)
ax.tick_params(axis='y', labelsize=16)

ax.set_xlabel('Clinical cases', fontsize=19, fontweight = "bold")
ax.set_ylabel('Date', fontsize=19, fontweight = "bold")

plt.tight_layout()
plt.show()
