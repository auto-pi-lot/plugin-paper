"""
Test sound latency
"""

from autopilot import external
from autopilot.stim.sound import jackclient
from autopilot.stim.sound import sounds
from autopilot.hardware.gpio import Digital_In, Digital_Out
from autopilot import prefs
import time
import sys
import argparse

def start_jack_server():
    jackd_process = external.start_jackd()
    server = jackclient.JackClient(disable_gc=True)
    server.start()
    return jackd_process, server

def test_sound(n_reps:int=-1, iti=0.5, duration:float=100):
    tone = sounds.Tone(10000, duration=duration, amplitude=0.1)
    tone.buffer()

    out_conf = prefs.get('HARDWARE')['GPIO']['digi_out']
    in_conf = prefs.get('HARDWARE')['GPIO']['digi_in']
    pin_out = Digital_Out(**out_conf)
    pin_in = Digital_In(**in_conf)

    def play_wrapper(*args):
        tone.play()
    pin_in.assign_cb(play_wrapper)

    n_loops = 0
    try:
        while n_reps < 0 or n_loops < n_reps:
            # could use pulse but want a longer pulse yno
            # pin_out.pulse()
            pin_out.set(True)
            # time.sleep(0.2)
            tone.stop_evt.wait(5)
            pin_out.set(False)
            tone.buffer()

            time.sleep(iti)
            n_loops += 1
    except KeyboardInterrupt:
        pass

    finally:
        pin_out.release()
        pin_in.release()


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        "Test Sound latency")
    parser.add_argument(
        '-n','--n_reps', help="Number of times to run each test",
        type=int, default=750, required=False)
    parser.add_argument(
        '-i', '--iti', help="Number of ms to wait in between each test",
        type=float, default=0.5, required=False
    )
    parser.add_argument(
        '-w', '--which', help="Which test to run? (integer, corresponds to tests viewable with --list)",
        type=int, default=0, required=False
    )
    parser.add_argument(
        '-l', '--list', help="List available jackd test settings",
        action='store_true', required=False
    )
    return parser


if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()

    TESTS = [
        "jackd -P75 -p16 -t2000 --silent -dalsa -dhw:sndrpihifiberry -P -r192000 -n 2 -s -p 32 &",
        "jackd -P75 -p16 -t2000 --silent -dalsa -dhw:sndrpihifiberry -P -r192000 -n 2 -s -p 64 &",
        "jackd -P75 -p16 -t2000 --silent -dalsa -dhw:sndrpihifiberry -P -r192000 -n 2 -s -p 128 &",
        "jackd -P75 -p16 -t2000 --silent -dalsa -dhw:sndrpihifiberry -P -r96000 -n 2 -s -p 32 &",
        "jackd -P75 -p16 -t2000 --silent -dalsa -dhw:sndrpihifiberry -P -r96000 -n 2 -s -p 64 &",
        "jackd -P75 -p16 -t2000 --silent -dalsa -dhw:sndrpihifiberry -P -r96000 -n 2 -s -p 128 &",
        "jackd -P75 -p16 -t2000 --silent -dalsa -dhw:sndrpihifiberry -P -r192000 -n 3 -s -p 32 &",
    ]

    if args.list:
        for i, test in enumerate(TESTS):
            print(f"{i}: {test}")
        sys.exit(0)

    test = TESTS[args.which]
    print(f'running test {args.which}:\n{test}')

    prefs.set('JACKDSTRING', TESTS[args.which])

    jackd_proc, server = start_jack_server()

    try:
        test_sound(args.n_reps, args.iti)

    finally:
        server.quit()
        jackd_proc.kill()