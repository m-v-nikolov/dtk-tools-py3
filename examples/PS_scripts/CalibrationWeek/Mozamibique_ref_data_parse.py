import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt


def read_data(csvfilename):
    df = pd.read_csv(csvfilename)
    # df1 = pd.read_csv('C://Users//pselvaraj//Dropbox (IDM)//Malaria Team Folder//data//Mozambique//Magude//Ento//mosquito_characteristics.csv')
    # df = df[df['trap_location'] == 1]    # Include indoor catches only

    return df


def plot_vector_counts_by_month(df, filename, savedirectory):
    df = df[['date', 'gambiae_count', 'funestus_count']]

    df['date'] = pd.to_datetime(df['date'])
    df['date'] = df.date.apply(lambda x: pd.to_datetime(x).strftime('%m/%Y'))
    df['date'] = pd.to_datetime(df['date'])
    df2 = df.groupby('date')['gambiae_count'].apply(np.sum).reset_index()
    df2['funestus_count'] = list(df.groupby('date')['funestus_count'].apply(np.sum))

    filepath = os.path.join(savedirectory, filename)

    plt.figure()
    plt.plot(df2['date'], df2['gambiae_count'], label='gambiae')
    plt.plot(df2['date'], df2['funestus_count'], color='k', label='funestus')
    plt.ylabel('Counts')
    plt.xlabel('Date')
    plt.title('Mosquito counts for Magude by month')
    plt.legend()
    plt.xticks(rotation=90)
    plt.savefig(filepath)


def plot_mosquito_counts_normalized_by_adult(df, filename, savedirectory):
    df = df[['date', 'gambiae_count', 'funestus_count', 'adult_house']]
    df['gambiae_count'] = df['gambiae_count']/df['adult_house']
    df['funestus_count'] = df['funestus_count'] / df['adult_house']
    df = df.dropna()

    df['date'] = pd.to_datetime(df['date'])
    df['date'] = df.date.apply(lambda x: pd.to_datetime(x).strftime('%m'))
    df['date'] = pd.to_datetime(df['date'])
    df2 = df.groupby('date')['gambiae_count'].apply(np.mean).reset_index()
    df2['funestus_count'] = list(df.groupby('date')['funestus_count'].apply(np.mean))

    filepath = os.path.join(savedirectory, filename)

    plt.figure()
    plt.plot(df2['date'], df2['gambiae_count'], label='gambiae')
    plt.plot(df2['date'], df2['funestus_count'], color='k', label='funestus')
    plt.ylabel('Counts')
    plt.xlabel('Date')
    plt.title('Mosquito counts for Magude by month normalized by number of adults')
    plt.legend()
    plt.xticks(rotation=90)
    plt.savefig(filepath)

if __name__=='__main__':
    csvfile = 'C://Users//pselvaraj//Dropbox (IDM)//Malaria Team Folder//data//Mozambique//Magude//Ento//mosquito_count_by_house_day.csv'
    savedir = 'C://Users//pselvaraj//Dropbox (IDM)//Malaria Team Folder//projects//Mozambique//entomology_calibration//Reference_data_figures'

    monthly_sum_plot_filename = 'Vector_counts_by_month.png'
    monthly_sum_norm_adults_plot_filename = 'Vector_counts_by_month_normalized.png'

    df = read_data(csvfile)
    # plot_vector_counts_by_month(df, monthly_sum_plot_filename, savedir)
    plot_mosquito_counts_normalized_by_adult(df, monthly_sum_norm_adults_plot_filename, savedir)
