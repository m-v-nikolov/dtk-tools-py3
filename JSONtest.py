import json
import pandas as pd
import numpy as np
# import os
from collections import OrderedDict
import itertools


fileName = 'C:/Users/pselvaraj/Desktop/MalariaSummaryReport_Monthly_Report.json'

json_data = open(fileName)
# json_data = open('C:/Users/pselvaraj/Desktop/MalariaSummaryReport_Monthly_Report.json')
data = json.load(json_data)

bins = OrderedDict([('Time', [i * 1 for i, _ in enumerate(data['Annual EIR'])]), ('Age Bins', data['Age Bins']), ('PfPR bins', data['Parasitemia Bins'])])
# bins['time'] = [i * 1 for i, _ in enumerate(data['Annual EIR'])]
bin_tuples = list(itertools.product(*bins.values()))
multi_index = pd.MultiIndex.from_tuples(bin_tuples, names=bins.keys())

channel = 'PfPR by Parasitemia and Age Bin'
channel_series = pd.Series(np.array(data[channel]).flat, index=multi_index, name=channel)
#
# channel_series = pd.Series(np.array(data[channel]).flatten(), index=multi_index, name=channel)
#
#
# ref_age_bins = [5,15,100]
# from calibtool.analyzers.Helpers import accumulate_ageseasonbins_cohort
#
seasons = [4,8,12]
#
# person_years, countsParasitemia = accumulate_ageseasonbins_cohort(
#     data['PfPR by Parasitemia and Age Bin'],
#     data['Average Population by Age Bin'],
#     ref_age_bins, seasons)
#
#
#
# df = pd.DataFrame({'A' : ['foo', 'bar', 'foo', 'bar','foo', 'bar', 'foo', 'foo'],'B' : ['one', 'one', 'two', 'three','two', 'two', 'one', 'three'],'C' : np.random.randn(8),'D' : np.random.randn(8)})
#
# fileName = 'C:/Eradication/simulations/ExampleCalibration_iter0_2016_11_03_10_34_10_725000/2016_11_03_10_34_11_038000/output/MalariaSummaryReport_Annual_Report.json'
# fileNamewrite = 'C:/Users/pselvaraj/Desktop/MalariaSummaryReport_Annual_Report.json'
#
# json_data = open(fileName)
# data = json.load(json_data)
# data['Metadata']['reporting_interval'] = [365]*len(data['Time']['Annual EIR'])
# with open(fileNamewrite, 'w') as outfile:
#     json.dump(data, outfile)

### From reference data to JSON
channel = 'PfPR by Parasitemia and Age Bin'
refdata = {        "density_by_age_and_season" : {
            "Metadata" : {
            "parasitemia_bins" : [0, 50, 500, 5000, 50000, 500000],
            "age_bins" : [5, 15, 100],
            "months"  : ['April','August','December']
            },
            "Seasons" : {
            "start_wet" : {
                "PfPR by Parasitemia and Age Bin" : [[2, 0, 0, 0, 1, 1], [4, 1, 2, 3, 2, 6], [7, 9, 4, 2, 4, 1]],
                "PfPR by Gametocytemia and Age Bin" : [[0, 0, 0, 5, 0, 0], [3, 9, 8, 1, 0, 0], [16, 4, 6, 1, 0, 0]]
            },
            "peak_wet" : {
                "PfPR by Parasitemia and Age Bin" : [[0, 1, 0, 1, 1, 0], [13, 1, 0, 3, 0, 1], [9, 12, 3, 0, 1, 0]],
                "PfPR by Gametocytemia and Age Bin" : [[1, 0, 1, 1, 0, 0], [2, 4, 8, 4, 1, 0], [7, 10, 5, 3, 0, 0]]
            },
            "end_wet" : {
                "PfPR by Parasitemia and Age Bin" : [[1, 0, 0, 0, 1, 0], [8, 1, 1, 6, 3, 1], [10, 11, 4, 2, 0, 0]],
                "PfPR by Gametocytemia and Age Bin" : [[1, 0, 0, 1, 0, 0], [7, 9, 3, 1, 0, 0], [14, 10, 3, 0, 0, 0]]
            }
            }
        }
    }
months = ['April','August','December']
required_reference_types = 'density_by_age_and_season'
data_types = refdata[required_reference_types].keys()
if 'by_age_and_season' in required_reference_types:
    Para = [[] for i in range(2)]
    bins = OrderedDict([('PfPR Type',['Parasitemia','Gametocytemia']),('Seasons', refdata[required_reference_types]['Seasons'].keys()),('Age Bins', refdata[required_reference_types]['Metadata']['age_bins']), ('PfPR bins', refdata[required_reference_types]['Metadata']['parasitemia_bins'])])
    for season in refdata[required_reference_types]['Seasons']:
        for Paratype in refdata[required_reference_types]['Seasons'][season].keys():
            if 'Gametocytemia' in Paratype:
                Para[1].append(refdata[required_reference_types]['Seasons'][season][Paratype])
            elif 'Parasitemia' in Paratype:
                Para[0].append(refdata[required_reference_types]['Seasons'][season][Paratype])
    bin_tuples = list(itertools.product(*bins.values()))
    multi_index = pd.MultiIndex.from_tuples(bin_tuples, names=bins.keys())
    ref_channel_series = pd.Series(np.array(Para).flatten(), index=multi_index,name=channel)

    ref_channel_series


df = channel_series.reset_index()
seasonIndex = []
for i in range(len(seasons)):
    seasonIndex.extend([t for t in range(seasons[i]-1,df.Time[-1:]+1,12)])

df = ref_channel_series.reset_index()
df = df[df.Time.isin(seasonIdfndex)]


df['Age Bins'] = pd.cut((df['Time']+1)/12, age_bins)
list(df.columns.values)

pop = [[i*10] for i in range(13)]
bins = OrderedDict([('Time', [i for i in range(13)]), ('Age Bins', [1000])])
# bins['time'] = [i * 1 for i, _ in enumerate(data['Annual EIR'])]
bin_tuples = list(itertools.product(*bins.values()))
multi_index = pd.MultiIndex.from_tuples(bin_tuples, names=bins.keys())
channel = 'Population by Age Bin'
ageSer = pd.Series(np.array(pop).flatten(), index=multi_index, name=channel)
ageSer = ageSer.reset_index()

pd.merge(df,ageSer,left_on='Time',right_on='Time')['Population by Age Bin']

pop = pd.merge(df_sim,df_pop,left_on=['Time','Age Bins'],right_on=['Time','Age Bins'])


df = pd.DataFrame(np.random.random((3,3)), columns=range(3))
df.columns = pd.MultiIndex.from_tuples([('a', 'b'), ('a', 'c'), ('b', 'd')])

fileName = 'C:/Users/pselvaraj/Downloads/OutputForSimId_5cefbe2b-d4d1-e411-93f9-f0921c16b9e7/output/MalariaSummaryReport_Annual_Report.json'

fileName = 'C:/Users/pselvaraj/Downloads/OutputForSimId_74edbe2b-d4d1-e411-93f9-f0921c16b9e7/output/MalariaSummaryReport_Annual_Report.json'
json_data = open(fileName)
# json_data = open('C:/Users/pselvaraj/Desktop/MalariaSummaryReport_Monthly_Report.json')
data = json.load(json_data)