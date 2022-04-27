from autopilot.hardware.gpio import Digital_Out, Digital_In
from autopilot import prefs
import numpy as np
import time
import timeit
import argparse
import typing
from pathlib import Path
from plugin_tests.scripts.helpers import Result, Results
from tqdm import tqdm, trange
import datetime
import json


def test_write(n_reps:int = 10000, result:bool=True, doprint:bool = True, iti:float = 1) -> Result:
    # get the configuration for our output pin from prefs.json
    pin_conf = prefs.get('HARDWARE')['GPIO']['digi_out']
    pin = Digital_Out(**pin_conf)
    set_to = True
    times = []
    for i in trange(n_reps, mininterval=1):
        start_time = time.perf_counter_ns()
        pin.set(set_to, result)
        times.append(time.perf_counter_ns() - start_time)
        set_to = not set_to
        time.sleep(iti/1000)

    if not result:
        test_name = "write_noresult"
    else:
        test_name = "write"

    result = Result(times=times, test=test_name)

    if doprint:
        print(result)

    return result


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        "Test GPIO Speed outside of a task/pilot context")
    parser.add_argument(
        '-n','--n_reps', help="Number of times to run each test",
        type=int, default=10000, required=False)
    parser.add_argument(
        '-i', '--iti', help="Number of ms to wait in between each test",
        type=float, default=1, required=False
    )
    parser.add_argument(
        '--quiet', help="Don't print results to stdout", action="store_false"
    )
    return parser


if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()

    results = Results(tests='gpio')
    try:
        results.append(test_write(n_reps=args.n_reps, result=True, doprint=args.quiet, iti=args.iti))
        results.append(test_write(n_reps=args.n_reps, result=False, doprint=args.quiet, iti=args.iti))
    finally:
        path = results.write()
        print(f"Wrote results to {str(path)}")
