import pandas as pd

def example_selection(timeseries):
    # note this is once-per-week snapshots, not weekly (running) averages...
    weekly=timeseries[::7]
    dates=pd.date_range('1/1/2000', periods=len(weekly), freq='W')
    return pd.Series(weekly,index=dates)