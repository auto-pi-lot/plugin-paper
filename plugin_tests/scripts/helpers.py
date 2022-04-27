from dataclasses import dataclass
import typing
import numpy as np

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

    def __str__(self) -> str:
        return (
            f"Test: {self.test}\nReps: {len(self.times)}\n"
            f"--------------\n"
            f"Mean: {np.round(self.mean/1000000, self.precision)}ms\n"
            f"Standard Deviation: +/-{np.round(self.std/1000000, self.precision)}"
            )