import pandas as pd

def example_selection(start_date='1/1/2000'):
    def f(timeseries):
        # N.B. defaults to once-per-week snapshots, not weekly (running) averages...
        weekly=timeseries[::7]
        dates=pd.date_range(start_date, periods=len(weekly),freq='W')
        return pd.Series(weekly,index=dates)
    return f