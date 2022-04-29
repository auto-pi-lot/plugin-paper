from pathlib import Path
import subprocess
import pandas as pd


def save_trace(ip:str, path:Path=Path('.'), base_name:str="OscTrace", mode:str="NORM"):
    # check for files in current directory
    current_files = list(path.glob('*.csv'))
    trace_n = 0
    if len(current_files)>0:
        trace_n = int(current_files[-1].stem.split('_')[-1]) + 1

    out_fn = f"{base_name}_{trace_n}.txt"

    subprocess.run(['ds1054z', 'save-data', '--filename', out_fn, '--mode', mode, ip])

def save_all_traces(
        ip:str,
        path:Path=Path('.'),
        base_name:str="OscTrace",
        mode:str="NORM") -> pd.DataFrame:
    """
    Save all traces recorded in the DS1054Z's recording memory

    Args:
        ip (str): IP address of oscilloscope
        path (:class:`pathlib.Path`): Directory to save trace in
        base_name (str): Base name of output files. Saved will will be of the form
            f"{base_name}_n.csv" where n increments for each successive call
        mode (str): One of

            * ``"NORM"`` - just traces on screen
            * ``"RAW"`` - full trace from memory (takes longer)
            * ``"MAX"`` - Tries to get RAW if possible, otherwise NORM

    Returns:
        (:class:`pandas.DataFrame`): A dataframe with timestamps (in seconds),
            voltages per channel, and a trace index.
    """
    osc = DS1054Z(ip)
    start_frame = int(osc.query(":FUNCtion:WREPlay:FSTart?"))
    end_frame = int(osc.query(":FUNCtion:WREPlay:FEND?"))

    traces = []
    for i in range(start_frame, end_frame+1):
        # Move to next trace
        osc.write(f":FUNCtion:WREPlay:FCURrent {i}")

        # Get each displayed channel's samples and timestamps
        data = {}
        data['time'] = osc.waveform_time_values_decimal
        for channel in osc.displayed_channels:
            data[f"CH_{channel}"] = osc.get_waveform_samples(channel, mode=mode)
        data["trace"] = i
        traces.append(pd.DataFrame(data))

    # concat all dataframes
    dfs = pd.concat(traces, ignore_index=True)

    # get a filename that increments in number based on existing files in directory
    current_files = list(path.glob(f'{base_name}*.csv'))
    trace_n = len(current_files)

    out_fn = path / f"{base_name}_{trace_n}.csv"
    dfs.to_csv(out_fn, index=False)
    return dfs





if __name__ == "__main__":
    from ds1054z import DS1054Z
    osc_ip = "192.168.0.163"
    save_trace(osc_ip)