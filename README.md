# plugin-paper

Plugin accompanying the [autopilot paper](https://github.com/auto-pi-lot/autopilot-paper), also see its [wiki entry](https://wiki.auto-pi-lot.com/index.php/Plugin:Autopilot_Paper)

To use, clone into your autopilot plugins directory (default `~/autopilot/plugins`) and then install
the dependencies from `pyproject.toml` using `pip` (`pip install .` from repository root) or poetry
(`poetry install` from repository root). If you have autopilot installed in a virtual environment you will need to activate
it first. (virtualenv: `source <venv_path>/bin/activate`, poetry: from the directory root, `poetry shell`)

# Contents

All within `plugin_paper`

## `analysis/`

A few helper functions that directly relate to the output of other code in the plugin repository.
The remainder of the analysis and plotting code for the paper can be found in [the paper repository](https://github.com/auto-pi-lot/autopilot-paper/tree/master/code).

* `combine_traces.py` - utility function to combine traces made over multiple recordings extracted by `scripts.save_trace`
* `latency` - from oscilloscope traces, find the latency from time = 0 to when the trace of interest crosses some threshold value.
  Used to calculate latencies presented in section 5 of the paper. 

## `hardware/`

Example hardware objects, can be used from within autopilot like `autopilot.get('hardware', 'Digital_Out_Zero')`

* `ds1000z.py` - Example of extending hardware classes to a new (`SCPI`) type, wrapper around [ds1054z](https://github.com/pklaus/ds1054z)
  and used to extract traces over the network from a [Rigol DS1054Z](wiki.auto-pi-lot.com/index.php/Rigol_DS1054Z) oscilloscope
* `zero.py` - Wrapper around [gpiozero](https://gpiozero.readthedocs.io/en/stable/) used in Section 4.1 of the paper and
  also by `test_gpio` described below

## `scripts/`

Scripts to run tests!

* `helpers.py` - a helper Results class for keeping track of (non-oscilloscope) results output
* `save_trace.py` - functional forms of the trace export also available in the `ds1000z.py` class. Export oscilloscope traces
  from an oscilloscope and save them to a .csv. file
* `test_gpio.py` - GPIO Tests described in section 5.1 of the paper

Run from the command line, which has the following help message:

```
usage: Test GPIO Speed outside of a task/pilot context [-h] [-n N_REPS] [-i ITI] [--quiet] [-w WHICH] [-t TIME]

optional arguments:
  -h, --help            show this help message and exit
  -n N_REPS, --n_reps N_REPS
                        Number of times to run each test
  -i ITI, --iti ITI     Number of ms to wait in between each test
  --quiet               Don't print results to stdout
  -w WHICH, --which WHICH
                        Which test (by index) to run. Otherwise run all
  -t TIME, --time TIME  How long to run the readwrite test (seconds)
```

Where the tests specified by `-w` are:

* `0` - `test_write` - test writing to a GPIO while also reading the resulting state
* `1` - `test_write` - test writing to a GPIO without reading the resulting state
* `2` - `test_write_zero` - test writing to a GPIO by the `Digital_Out_Zero` class described above
* `3` - `test_readwrite` - test latency from an external input digital signal and digital output
* `4` - `test_readwrite_script` - test above latency using a pigpiod script
* `5` - `test_series_jitter` - test jitter when opening and closing a digital_output using a pigpiod script. Not included
  in the paper because it is functionally identical to other jitters (specifically `test_readwrite_script`) already reported

tests `0`-`2` return a `Results` object because they measure software timestamps, but the rest return
an empty results object because the measurements are done externally with an oscilloscope.

* `test_sound.py` - Scripts to test sound latency, reported in section 4.3

Run from the command line, with the following help message:

```
usage: Test Sound latency [-h] [-n N_REPS] [-i ITI] [-w WHICH] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -n N_REPS, --n_reps N_REPS
                        Number of times to run each test
  -i ITI, --iti ITI     Number of ms to wait in between each test
  -w WHICH, --which WHICH
                        Which test to run? (integer, corresponds to tests viewable with --list)
  -l, --list            List available jackd test settings
```

The test requires you to have `AUDIOSERVER = 'jack'` in `autopilot.prefs`, and have `jackd` installed
using `python -m autopilot.setup.run_script jackd_source`. It assumes you're using the [HiFiBerry Amp 2](wiki.auto-pi-lot.com/index.php/HiFiBerry_Amp2) 
described in the manuscript (ie. has `-dhw:sndrpihifiberry` hardcoded in the jackd launch strings).

the `--which` flag switches between several different configurations of jackd audio. The main thing that
changes between them is the sampling rate and the size of the buffer period. Only test `0` is reported in the 
manuscript, though the rest of the tests were run to verify that that result wasn't a one-off and the rest of them
behave qualitatively similarly (although, of course, increasing buffer sizes result in longer latencies).


| `--which` | `-r` (sampling rate) | `-p` (samples per period) | `-n` (periods per buffer) |
|-----------|----------------------|---------------------------|---------------------------|
| 0         | 192000 | 32 | 2 |
| 1         | 192000 | 64 | 2 |
| 2         | 192000 | 128 | 2 |
| 3         | 96000 | 32 | 2 |
| 4         | 96000 | 64 | 2 |
| 5         | 96000 | 128 | 2 |
| 6         | 192000 | 32 | 3 |

## `tasks/`

Contains only one task, `Network_Latency` within `tasks/network`. Create a protocol from the autopilot
terminal GUI, or else put the following `.json` in your protocols directory (default `~/autopilot.protocols`).
Then assign the task to some subject using `Subject.assign_task` or do the same from the Terminal GUI (the + button on a given pilot)

Assumes you have two pilots setup and connected to a running terminal (used for connecting the leader to the follower).
On task start, the leader sends a multihop message routed through the terminal to the follower (specified in the `follower_id` param),
and then upon receiving the response, the leader will start sending messages to the follower, and the send and receive time are
compared to compute latency.

Assumes both pilots are on a relatively quiet local network and that they have configured local NTP synchronization
(see the [wiki](https://wiki.auto-pi-lot.com/index.php/NTP) for documentation), otherwise the measured latency
will only be as accurate as the relative synchronization of their clocks.

### protocol

```json
[
    {
        "graduation": {
            "type": "NTrials",
            "value": {
                "n_trials": "99999999",
                "type": "NTrials"
            }
        },
        "n_messages": 10000,
        "iti": 10,
        "step_name": "Network_Latency",
        "task_type": "Network_Latency",
        "follower_id": "paper_tester_1"
    }
]
```

### Params:

* `n_messages` - int - Number of messages to send back and forth
* `follower_id` - str - ID of the pilot that will be used as the follower, needed to route the start message to it
* `iti` - float - inter-trial interval, in ms

### TrialData

The schema for the collected trial data (`.TrialData.schema()`) is:

```python
schema = {'description': 'Base class for declaring trial data.\n'
                '\n'
                'Tasks should subclass this and add any additional parameters '
                'that are needed.\n'
                'The subject class will then use this to create a table in the '
                'hdf5 file.',
 'properties': {'group': {'description': 'Path of the parent step group',
                          'title': 'Group',
                          'type': 'string'},
                'latency': {'description': 'Difference between receive and '
                                           'send time, in ms',
                            'title': 'Latency',
                            'type': 'number'},
                'recv_time': {'description': 'Timestamp of when the message '
                                             'was received by the second pi',
                              'format': 'date-time',
                              'title': 'Recv Time',
                              'type': 'string'},
                'send_time': {'description': 'Timestamp of sending the initial '
                                             'message',
                              'format': 'date-time',
                              'title': 'Send Time',
                              'type': 'string'},
                'session': {'description': 'Current training session, '
                                           'increments every time the task is '
                                           'started',
                            'title': 'Session',
                            'type': 'integer'},
                'session_uuid': {'description': 'Each session gets a unique '
                                                'uuid, regardless of the '
                                                'session integer, to enable '
                                                'independent addressing of '
                                                'sessions when session numbers '
                                                'might overlap (eg. '
                                                'reassignment)',
                                 'title': 'Session Uuid',
                                 'type': 'string'},
                'trial_num': {'datajoint': {'key': True},
                              'description': 'Trial data is grouped within, '
                                             'well, trials, which increase '
                                             '(rather than resetting) across '
                                             'sessions within a task',
                              'title': 'Trial Num',
                              'type': 'integer'}},
 'required': ['session', 'trial_num', 'send_time', 'recv_time', 'latency'],
 'title': 'TrialData',
 'type': 'object'}
```







