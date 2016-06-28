import pandas as pd


# convert a dictionary to a data frame, with index set to dictionary keys
# extend to "multi dictionaries" (dictionaries of dictionaries of dictionaries of ...)
# via pandas MultiIndex (?)

def dict2pd(d):
    return pd.DataFrame.from_dict(d, orient='index')
