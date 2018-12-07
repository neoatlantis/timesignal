#!/usr/bin/env python3

import numpy

class FourierFilter:

    def __init__(self, samplerate, windowSize):
        dt = 1 / samplerate
        N = windowSize
        T = dt * N
        df = 1 / T
        self.f_scale = list((numpy.fft.fftfreq(N) * N * df)[:int(N/2)])

    def measure(self, series):
        s = numpy.fft.rfft(series)
        return lambda f: s[self.f_scale.index(f)]
