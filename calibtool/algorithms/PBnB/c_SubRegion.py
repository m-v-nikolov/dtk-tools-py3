# -*- coding: utf-8 -*-
"""
Created on Fri Jun 23 14:21:27 2017

@author: TingYu Ho
"""

class c_SubRegion(object): 
    def __init__(self, coordinate_lower, coordinate_upper, params):
        import pandas as pd  # this is how I usually import pandas
        import numpy as np
        self.s_label = 'C'  # C: undetermined, P:prune, M:maintain
        self.i_index = 0
        self.b_activate = True  # become false if branching into two
        self.b_branchable = True
        self.b_elite = False
        self.b_worst = False
        self.b_maintaining_indicator = False  # prepared to maintain in this time
        self.b_pruning_indicator = False  # prepared to prune in this time
        self.l_sample = []  # list of sampling points in this subregion
        self.l_coordinate_lower = coordinate_lower  # lower bound of this region
        self.l_coordinate_upper = coordinate_upper  # upper bound of this region
        self.array_distance = np.array(self.l_coordinate_upper)-np.array(self.l_coordinate_lower)
        self.f_volume = np.prod(self.array_distance[self.array_distance != 0])  # volume of the subregion
        self.i_min_sample = 0  # minimum value of sampling points in this subregions
        self.i_max_sample = 0  # maximum value of sampling points in this subregions
        self.f_min_diff_sample_mean = 0.  # minimum value of difference of sorted sampling points in this subregions
        self.f_max_var = 0.   # maximum value of variance of sampling points in this subregions
        self.pd_sample_record = pd.DataFrame([], columns=[p['Name'] for p in params]+['rep']+['mean']+['var']+['SST'])
        self.pd_sample_record['rep'].astype(int)
        self.pd_sample_record['mean'].astype(float)
        self.pd_sample_record['var'].astype(float)
        self.pd_sample_record['SST'].astype(float)
