#!/usr/bin/env python3

from math import sqrt
import numpy


class WalshFilter:

    def __init__(self, framesPerPeriod, windowSize):
        halfperiod = int(framesPerPeriod / 2)
        self.walsh1 = numpy.array([
            1 if int(i / halfperiod) % 2 else -1
            for i in range(0, windowSize)
        ])
        self.walsh2 = numpy.array([
            1 if int(i / halfperiod + 0.25) % 2 else -1
            for i in range(0, windowSize)
        ])

    def measure(self, series):
        assert len(series) == len(self.walsh1)
        t1 = self.walsh1 * series
        t2 = self.walsh2 * series
        return sqrt(sum(t1) ** 2 + sum(t2) ** 2) # no average, sum value enough
