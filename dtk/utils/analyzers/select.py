import pandas as pd

def example_selection(start_date='1/1/2000', freq='W'):
    def f(timeseries):
        # N.B. once-per-period snapshots, not period-sliding-window averages...
        freq_days = {'W': 7, 'M': 30, 'D': 1, 'Y': 365}
        freq_sliced = timeseries[::freq_days[freq.upper()]]
        dates = pd.date_range(start_date, periods=len(freq_sliced), freq=freq)
        return pd.Series(freq_sliced, index=dates)
    return f

def summary_interval_selection(start_date='1/1/2000', freq='M'):
    def f(ts):
        dates = pd.date_range(start_date, periods=len(ts), freq=freq)
        return pd.Series(ts, index=dates)
    return f