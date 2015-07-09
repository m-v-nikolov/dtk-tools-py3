import pandas as pd

def example_selection(start_date='1/1/2000'):
    def f(timeseries):
        # N.B. once-per-week snapshots, not weekly (running) averages...
        weekly = timeseries[::7]
        dates = pd.date_range(start_date, periods=len(weekly), freq='W')
        return pd.Series(weekly, index=dates)
    return f

def summary_interval_selection(start_date='1/1/2000', freq='M'):
    def f(ts):
        dates = pd.date_range(start_date, periods=len(ts), freq=freq)
        return pd.Series(ts, index=dates)
    return f