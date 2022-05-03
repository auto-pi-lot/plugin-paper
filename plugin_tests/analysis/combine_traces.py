"""
Functions to combine traces extraced from tthe Rigol DS1054Z using the
:func:`~.save_trace.save_all_traces` function
"""

from pathlib import Path
import pandas as pd

def combine_traces(path:Path) -> pd.DataFrame:
    """
    Combine a directory of oscilloscope traces extracted using
    :func:`~.save_trace.save_all_traces`

    Args:
        path (:class:`pathlib.Path`): Directory containing .csv traces

    Returns:
        :class:`pandas.DataFrame` of combined traces
    """

    path = Path(path)
    trace_files = path.glob('*.csv')
    traces = []
    for i, file in enumerate(trace_files):
        trace = pd.read_csv(file)
        trace['recording'] = i
        trace['file'] = str(file)
        traces.append(trace)

    return pd.concat(traces)

