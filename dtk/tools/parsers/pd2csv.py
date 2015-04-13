# convert a pandas data frame to a csv file
def pd2csv(df, dst="dataframe.csv", chunksize=10):

# please check the documentation at 
# http://pandas.pydata.org/pandas-docs/dev/generated/pandas.DataFrame.to_csv.html

# for information on the default parameters used below

    df.to_csv(dst, sep=',', na_rep='', float_format='.2f', header=True, index=True, mode='w', line_terminator='\n', chunksize=chunksize, doublequote=True, decimal='.')