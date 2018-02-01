import os
import logging

import numpy as np
import pandas as pd
import geopandas
from shapely.geometry import Point

log = logging.getLogger(__name__)


data_directory = os.path.join(os.path.expanduser('~'), 'Dropbox (IDM)',
                              'Malaria Team Folder', 'data',
                              'Mozambique', 'Magude')


def yes_no_dont_know_to_0_1_nan(s):
    """ Change 1 (yes), 2 (no), 3 (don't know) to 0 (no), 1 (yes) """

    s[s == 3] = np.nan
    s[s == 2] = 0

    return s


def get_compound_data():

    cmpd_df = pd.read_csv(os.path.join(data_directory, 'Ento', 'mosquito_count_by_house_day.csv'))

    cmpd_df = cmpd_df[cmpd_df['trap_location'] == 1]

    cmpd_df = cmpd_df[['date', 'gambiae_count', 'funestus_count', 'house_id', 'coordinates_lat', 'coordinates_lng']]
    groupbylist = ['date', 'house_id', 'coordinates_lat', 'coordinates_lng']

    cmpd_df['date'] = pd.to_datetime(cmpd_df['date'])
    cmpd_df['date'] = cmpd_df.date.apply(lambda x: pd.to_datetime(x).strftime('%m/%Y'))
    cmpd_df['date'] = pd.to_datetime(cmpd_df['date'])
    df = cmpd_df.groupby(groupbylist)['gambiae_count'].apply(np.sum).reset_index()
    df['funestus_count'] = list(cmpd_df.groupby(groupbylist)['funestus_count'].apply(np.sum))

    return df


def get_individual_data():

    ind_df = pd.read_csv(os.path.join(data_directory, 'Members', 'census_mda_members.csv'),
                         index_col='ID', low_memory=False)

    ind_df['sleep_under_net_r2'] = yes_no_dont_know_to_0_1_nan(ind_df['sleep_under_net_r2'])  # standardize with sleep_under_net_r1

    # for usage denominators
    for rnd in range(1, 3):
        ind_df['answered_under_net_r%d' % rnd] = pd.notnull(ind_df['sleep_under_net_r%d' % rnd])
    for rnd in range(1, 5):
        ind_df['answered_under_net_mda%d' % rnd] = pd.notnull(ind_df['sleep_under_net_mda%d' % rnd])

    log.debug(ind_df.head())

    return ind_df


def geodf_from_df(cmpd_df, rnd):

    if rnd not in [1, 2]:
        raise Exception('Only know latitude/longitude for census rounds 1 and 2 (not %d)' % rnd)

    geometry = [Point(xy) for xy in zip(cmpd_df['lng_r%d' % rnd], cmpd_df['lat_r%d' % rnd])]
    crs = {'init': 'epsg:4326'}
    cmpd_gdf = geopandas.GeoDataFrame(cmpd_df, crs=crs, geometry=geometry)

    return cmpd_gdf
