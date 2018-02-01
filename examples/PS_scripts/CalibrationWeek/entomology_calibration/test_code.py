import pandas as pd
import os
import numpy as np
import datetime
import calendar

import json
from calibtool.analyzers.Helpers import season_channel_age_density_csv_to_pandas, convert_to_counts, age_from_birth_cohort, age_from_birth_cohort, season_from_time, aggregate_on_index

# dir = 'C://Users//pselvaraj//Desktop'
# filename = 'ReportVectorStats.csv'
# filepath = os.path.join(dir, filename)
#
# data = pd.read_csv(filepath, delimiter=',', encoding="utf-8-sig").reset_index()
# data = data[365:]
# data['Day'] = data['Time'].apply(lambda x: (x+1)%365)
# data = data[['Day', ' Population', ' VectorPopulation']]
# data['Vector_per_Human'] = data[' VectorPopulation']/data[' Population']
# data = data.groupby('Day')['Vector_per_Human'].apply(np.mean).reset_index()
#
# dateparser = lambda x: datetime.datetime.strptime(x, '%j').month
# data['Month'] = data['Day'].apply(lambda x: calendar.month_abbr[dateparser(str(x+1))])
# data = data.groupby('Month')['Vector_per_Human'].apply(np.mean).reset_index()


metadata = {
        'parasitemia_bins': [0, 50, 200, 500, np.inf],  # (, 0] (0, 50] ... (50000, ]
        'age_bins': [0, 5, 15, np.inf],  # (, 5] (5, 15] (15, ],
        'seasons': ['DC2', 'DH2', 'W2'],
        'seasons_by_month': {
            'May': 'DH2',
            'September': 'W2',
            'January': 'DC2'
        },
        'village': 'Matsari'
    }

reference_csv = 'C://Github//PS_dtk_tools//dtk-tools-malaria//malaria//study_sites//inputs//GarkiDB_data//GarkiDBparasitology.csv'
reference = season_channel_age_density_csv_to_pandas(reference_csv, metadata)

# csvfilename = 'c:////github////ps_dtk_tools////dtk-tools-malaria////malaria////study_sites////inputs////Mozambique_ento_data////mosquito_count_by_house_day.csv'
# df = pd.read_csv(csvfilename)
#
# metadata = {
#         'village': 'Magude',
#         'months': [calendar.month_abbr[i] for i in range(1, 13)],
#         'species': ['gambiae', 'funestus']
#     }
#
# df = df[['date', 'gambiae_count', 'funestus_count', 'adult_house']]
# df['gambiae'] = df['gambiae_count'] / df['adult_house']
# df['funestus'] = df['funestus_count'] / df['adult_house']
# df = df.dropna()
#
# df['date'] = pd.to_datetime(df['date'])
# dateparser = lambda x: int(x.strftime('%m'))
# df['Month'] = df['date'].apply(lambda x: calendar.month_abbr[int(dateparser(x))])
# df2 = df.groupby('Month')['gambiae'].apply(np.mean).reset_index()
# df2['funestus'] = list(df.groupby('Month')['funestus'].apply(np.mean))
#
# # Keep only species requested
# for spec in metadata['species']:
#     df1 = df2[['Month', spec]]
#     df1 = df1.rename(columns={spec: 'Counts'})
#     df1['Channel'] = [spec] * len(df1)
#     if 'dftemp' in locals():
#         dftemp = pd.concat([dftemp, df1])
#     else:
#         dftemp = df1.copy()
#
# dftemp = dftemp.set_index(['Channel', 'Month'])
from dtk.utils.parsers.malaria_summary import summary_channel_to_pandas

population_channel = 'Average Population by Age Bin'

ref_ix = reference.index
channels_ix = ref_ix.names.index('Channel')
channels = ref_ix.levels[channels_ix].values
seasons = {
            'May': 'DH2',
            'September': 'W2',
            'January': 'DC2'
        }

file = 'C://Users//pselvaraj//Desktop//MalariaSummaryReport_Monthly_Report.json'
data = json.load(open(file))

# Population by age and time series (to convert parasite prevalence to counts)
population = summary_channel_to_pandas(data, population_channel)

# Coerce channel data into format for comparison with reference
channel_data_dict = {}
for channel in channels:

    # Prevalence by density, age, and time series
    channel_data = summary_channel_to_pandas(data, channel)

        # Calculate counts from prevalence and population
    channel_counts = convert_to_counts(channel_data, population)

    # Reset multi-index and perform transformations on index columns
    df = channel_counts.reset_index()
    df = age_from_birth_cohort(df)  # calculate age from time for birth cohort
    df = season_from_time(df, seasons=seasons)  # calculate month from time

    # Re-bin according to reference and return single-channel Series
    rebinned = aggregate_on_index(df, reference.loc(axis=1)[channel].index, keep=[channel])
    channel_data_dict[channel] = rebinned[channel].rename('Counts')

sim_data = pd.concat(channel_data_dict.values(), keys=channel_data_dict.keys(), names=['Channel'])
sim_data = pd.DataFrame(sim_data)  # single-column DataFrame for standardized combine/compare pattern
