from autopilot.hardware import Hardware
from ds1054z import DS1054Z as DS1054Z_
from pathlib import Path
import typing
import pandas as pd

class SCPI(Hardware):
    """Metaclass for SCPI-based hardware devices"""


class DS1054Z(SCPI):
    """
    The `Rigol DS1054 Oscilloscope <https://www.rigolna.com/products/digital-oscilloscopes/1000z/`_

    See the `Wiki page <https://wiki.auto-pi-lot.com/index.php/Rigol_DS1054Z>`_ for more information

    Just an example class of implementing a new type of hardware object, does not implement all
    functionality of the Oscilloscope, just saving traces. See the
     `ds1054z package <https://github.com/pklaus/ds1054z>`_ we're using for more information.
    """
    TRACE_MODES = typing.Literal['NORM', 'RAW', 'MAX']

    def __init__(self, ip:str, **kwargs):
        super(DS1054Z, self).__init__(**kwargs)

        self.ip = ip
        self.scope = DS1054Z_(self.ip)

    def __getattr__(self, item:str):
        """If we don't have the method in this class, try and use the device's methods"""
        return getattr(self.scope, item)

    def save_traces(self,
            path: typing.Optional[Path] = None,
            frames: typing.Optional[typing.List[int]] = None,
            mode: TRACE_MODES = "NORM") -> pd.DataFrame:
        """
        Save all traces recorded in the DS1054Z's recording memory

        Args:
            path (:class:`pathlib.Path`): File (.csv) to save traces in, if present.
            frames (int, list[int]): Optional: Frame number or list of frames to save. If ``None`` (default), get all.
            mode (str): One of

                * ``"NORM"`` - just traces on screen
                * ``"RAW"`` - full trace from memory (takes longer)
                * ``"MAX"`` - Tries to get RAW if possible, otherwise NORM

        Returns:
            (:class:`pandas.DataFrame`): A dataframe with timestamps (in seconds),
                voltages per channel, and a trace index.
        """
        start_frame = int(self.scope.query(":FUNCtion:WREPlay:FSTart?"))
        end_frame = int(self.scope.query(":FUNCtion:WREPlay:FEND?"))

        traces = []
        all_frames = list(range(start_frame, end_frame+1))
        if frames is None:
            get_frames = all_frames
        else:
            if isinstance(frames, int):
                frames = [frames]
            # check if we requested frames that aren't present
            incorrect_frames = set(frames) - set(all_frames)
            if len(incorrect_frames)>0:
                err_txt = f"Frames {incorrect_frames} not in frames available on oscillocope, {start_frame} - {end_frame}"
                self.logger.exception(err_txt)
                raise ValueError(err_txt)
            get_frames = frames

        for i in get_frames:
            # Move to next trace
            self.scope.write(f":FUNCtion:WREPlay:FCURrent {i}")

            # Get each displayed channel's samples and timestamps
            data = {}
            data['time'] = self.scope.waveform_time_values_decimal
            for channel in self.scope.displayed_channels:
                data[f"CH_{channel}"] = self.scope.get_waveform_samples(channel, mode=mode)
            data["trace"] = i
            traces.append(pd.DataFrame(data))

        # concat all dataframes
        dfs = pd.concat(traces, ignore_index=True)

        # get a filename that increments in number based on existing files in directory
        if path is not None:
            try:
                path = Path(path).with_suffix('.csv')
                dfs.to_csv(path, index=False)
            except:
                self.logger.exception(f"Could not save traces to {str(path)}")

        return dfs
