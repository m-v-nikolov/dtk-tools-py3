import logging

import matplotlib.pyplot as plt

from spatial.plotting import plot_HH_maps
from spatial.parsing import get_compound_data, get_individual_data


def explore_households(savedir):

    cmpd_df = get_compound_data()

    plot_HH_maps(cmpd_df, savedir)


# def explore_members():
#
#     ind_df = get_individual_data()
#
#     columns = ['ID_hh'] \
#             + ['sleep_under_net_r%d' % x for x in range(1, 3)] \
#             + ['answered_under_net_r%d' % x for x in range(1, 3)] \
#             + ['sleep_under_net_mda%d' % x for x in range(1, 5)] \
#             + ['answered_under_net_mda%d' % x for x in range(1, 5)]
#
#     HH_sum_df = ind_df[columns].groupby('ID_hh').sum()
#
#     for rnd in range(1, 3):
#         HH_sum_df['itn_r%d' % rnd] = HH_sum_df['sleep_under_net_r%d' % rnd] / HH_sum_df['answered_under_net_r%d' % rnd]
#     for rnd in range(1, 5):
#         HH_sum_df['itn_mda%d' % rnd] = HH_sum_df['sleep_under_net_mda%d' % rnd] / HH_sum_df['answered_under_net_mda%d' % rnd]
#
#     cmpd_df = get_compound_data().join(HH_sum_df)
#
#     plot_HH_maps(cmpd_df, ['itn_r%d' % x for x in range(1, 3)])
#     plot_HH_maps(cmpd_df, ['itn_mda%d' % x for x in range(1, 5)])


if __name__ == '__main__':

    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    savedir = 'C://Users//pselvaraj//Dropbox (IDM)//Malaria Team Folder//projects//Mozambique//entomology_calibration//Reference_data_figures//Vector_spread'

    explore_households(savedir)
    # explore_members()

    # plt.show()
