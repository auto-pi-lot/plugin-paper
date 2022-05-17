"""
Helper functions for computing oscilloscope latencies combined with :mod:`.combine_traces`
"""

import pandas as pd
import numpy as np


def minmax(df:pd.DataFrame, col:str, groupby:tuple=('trace', 'recording')) -> pd.DataFrame:
    df[col] = df.groupby(list(groupby))[col].transform(
        lambda x: (x-x.min())/(x.max()-x.min())
    )
    return df

def extract_latencies(traces:pd.DataFrame,
                      response_col:str="CH_CHAN1",
                      groupby:tuple=('trace', 'recording'),
                      threshold:float=0.5,
                      minmax_:bool=False) -> pd.DataFrame:
    """Assuming the time of the trigger is 0, find the time that the response column first crosses the threshold"""

    # normalize both traces to 0-1
    if minmax_:
        traces = minmax(traces, response_col)

    latencies = []
    groups = []
    for i, group in traces.groupby(list(groupby)):
        try:
            idx = np.where(group[response_col] > threshold)[0]
            latencies.append(group['time'].iloc[idx[0]])
            groups.append(i)
        except IndexError:
            latencies.append(None)
            groups.append(i)

    return pd.DataFrame({'group': groups, 'latencies':latencies})






