from dataclasses import dataclass, field
import typing
import numpy as np
from pathlib import Path
from datetime import datetime
from autopilot import prefs
import json

@dataclass
class Result:
    """Results of an individual test"""
    times: typing.List[int]
    """
    Times (in ns) for each run of a test
    """
    test:str
    """
    Name of the test that was run
    """
    precision: typing.Optional[int] = 3
    """
    Precision of results printed in __str__
    """

    @property
    def mean(self) -> float:
        return float(np.mean(self.times))

    @property
    def std(self) -> float:
        return float(np.std(self.times))

    def dict(self) -> dict:
        return {
            'test': self.test,
            'times': self.times,
            'mean': self.mean,
            'std': self.std,
            'n_reps': len(self.times)
        }

    def __str__(self) -> str:
        topsep = "="*40 + "\n"
        midsep = '-'*40 + "\n"
        return topsep + \
            f"Test: {self.test}\nReps: {len(self.times)}\n" + \
            midsep + \
            (
                f"Mean: {np.round(self.mean/1000000, self.precision)}ms\n"
                f"Standard Deviation: +/-{np.round(self.std/1000000, self.precision)}\n"
            ) + \
            topsep

@dataclass
class Results:
    tests: str
    results: typing.Optional[typing.List[Result]] = field(default_factory=list)

    def append(self, result:Result):
        self.results.append(result)

    def dict(self) -> typing.List[dict]:
        return [r.dict() for r in self.results]

    def write(self, path:typing.Optional[Path]=None):
        if not path:
            path = Path(prefs.get('DATADIR')) / f"tests-{self.tests}-{datetime.now().strftime('%y%m%dT%H%M%S')}.json"

        with open(path, 'w') as jpath:
            json.dump(self.dict(), jpath)

        return path