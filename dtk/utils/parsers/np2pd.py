import pandas as pd

def np2pd(arr, to_series = False):

    
    # the array is flatten and converted to single pandas series
    if to_series:
        return pd.Series(arr.flatten())
    
    
    # otherwise, the array is converted to a pandas data frame
    # each row in the array is a row in the data frame
    #
    # assume 2D numpy arrays
    # (extend to arbitrary dimensions using panda's MultiIndex (?)
    # column labels are set by pandas defaults
    
    return pd.DataFrame(arr) 