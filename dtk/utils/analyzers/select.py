import pandas as pd

    def f(timeseries):
        # N.B. defaults to once-per-week snapshots, not weekly (running) averages...
        return pd.Series(weekly,index=dates)
    return f