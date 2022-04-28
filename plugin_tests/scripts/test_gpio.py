from autopilot.hardware.gpio import Digital_Out, Digital_In
from autopilot import prefs
from plugin_tests.hardware.zero import Digital_Out_Zero
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



def test_write(n_reps:int = 10000, result:bool=True, doprint:bool = True, iti:float = 0.001) -> Result:
    # get the configuration for our output pin from prefs.json
    pin_conf = prefs.get('HARDWARE')['GPIO']['digi_out']
    pin = Digital_Out(**pin_conf)
    set_to = True
    times = []
    for i in range(n_reps):
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


def test_write_zero(n_reps:int = 10000, doprint:bool = True, iti:float = 0.001) -> Result:
    """Same thing as above but with Digital Out Zero, sorry this isn't more reusable it's just a test!"""
    # get the configuration for our output pin from prefs.json
    pin_conf = prefs.get('HARDWARE')['GPIO']['digi_out']
    pin = Digital_Out_Zero(**pin_conf)
    set_to = True
    times = []
    for i in range(n_reps):
        start_time = time.perf_counter_ns()
        pin.set(set_to)
        times.append(time.perf_counter_ns() - start_time)
        set_to = not set_to
        time.sleep(iti/1000)

    test_name = "write_zero"

    result = Result(times=times, test=test_name)

    if doprint:
        print(result)

    return result

def test_readwrite(n_reps:int = 10000, doprint:bool = True, iti:float = 0.001) -> Result:
    """Test latency from external digital input to digital output"""
    out_conf = prefs.get('HARDWARE')['GPIO']['digi_out']
    in_conf = prefs.get('HARDWARE')['GPIO']['digi_in']
    pin_out = Digital_Out(**out_conf)
    pin_in = Digital_In(**in_conf)

    n_times = 0

    def turn_on_off(*args):
        global n_times
        print('hey')
        pin_out.set(True)
        time.sleep(0.001)
        pin_out.set(False)
        n_times += 1

    # cb = lambda: print('hey');pin_out.set(True)
    pin_in.assign_cb(turn_on_off, )

    pin_out.set(False)

    while n_times < n_reps:
        time.sleep(0.5)


    return Result([0], test="readwrite")
        

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
    parser.add_argument(
        '-w', "--which", help="Which test (by index) to run. Otherwise run all",
        type=int, required=False
    )
    return parser


if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()

    results = Results(tests='gpio')

    tests = [
        lambda: test_write(n_reps=args.n_reps, result=True, doprint=args.quiet, iti=args.iti),
        lambda: test_write(n_reps=args.n_reps, result=False, doprint=args.quiet, iti=args.iti),
        lambda: test_write_zero(n_reps=args.n_reps, doprint=args.quiet, iti=args.iti),
        lambda: test_readwrite(n_reps=args.n_reps)
    ]

    if args.which:
        tests = [tests[args.which]]

    try:
        for test in tests:
            results.append(test())

    finally:
        path = results.write()
        print(f"Wrote results to {str(path)}")
