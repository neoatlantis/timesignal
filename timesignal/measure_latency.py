#!/usr/bin/env python3

from math import pi, sin, sqrt, log
import sounddevice as sd
import numpy
import time

from .constants import *
#from .walsh_filter import WalshFilter
from .fft_filter import FourierFilter
from .phase_diff import phaseDiff

def andGate(array1, array2):
    assert len(array1) == len(array2)
    for i in range(0, len(array1)):
        yield 1 if array1[i] and array2[i] else 0

def schmidtTrigger(values, rise=0.6, fall=0.5):
    v = 0
    for x in values:
        if v == 0 and x > rise:
            v = 1
        elif v == 1 and x < fall:
            v = 0
        yield v

##############################################################################

def measureLatencyOnce(
    samplerate=SAMPLERATE,
    duration=10,
    frequency=SIGNAL_FREQUENCY,
    dtype=DATATYPE,
    windowSizeAsPeriods=5,
    verbose=False
):

    period = int(SAMPLERATE/SIGNAL_FREQUENCY)
    halfperiod = int(period/2)
    periodCount = windowSizeAsPeriods 
    windowSize = period * periodCount

    """walshFilter = WalshFilter(
        framesPerPeriod=period, # e.g. period of 1kHz signal, in frames
        windowSize=windowSize
    )
    walshFilter2 = WalshFilter(
        framesPerPeriod=halfperiod,
        windowSize=windowSize
    )"""
    fourierFilter = FourierFilter(
        samplerate=samplerate,
        windowSize=windowSize
    )


    with sd.InputStream(
        samplerate=samplerate,
        channels=2,
        dtype=dtype
    ) as stream:
        startT = time.time()
        sample, _ = stream.read(SAMPLERATE * duration)
        endT = time.time()
        sample = numpy.array([e[0] for e in sample])

        result = []
        result2 = []
        for i in range(0, len(sample)-1, windowSize):
            fftmeasure = fourierFilter.measure(sample[i:i+windowSize])
            result.append(fftmeasure(1000))
            result2.append(fftmeasure(2000))

        """for i in range(0, len(sample)-1, windowSize):
            result.append(walshFilter.measure(
                [e[0] for e in sample[i:i+windowSize]]
            ))
            result2.append(walshFilter2.measure(
                [e[0] for e in sample[i:i+windowSize]]
            ))"""

    def normalize(s):
        max1, min1 = max(s), min(s)
        return [(e - min1) / (max1 - min1) for e in s]

    a1 = normalize([abs(e) for e in result])
    #p1 = normalize([e[1] for e in result])
    a2 = normalize([abs(e) for e in result2])
    #p2 = normalize([e[1] for e in result2])
    #pd = normalize([p1[i] -p2[i] for i in range(0, len(result))])

    covResult = normalize([a1[i] * a2[i] for i in range(0, len(result))])
    covAverage = sum(covResult) / len(covResult)

    riseT = min(covAverage * 10, 0.4)
    fallT = max(riseT - 0.1, 0.1)

    sampleSignal = list(schmidtTrigger(covResult, rise=riseT, fall=fallT))

    if verbose:
        for i in range(0, len(result)):
            print(a1[i], a2[i], covResult[i], sampleSignal[i])
        exit()

    """
    # Use schmidt trigger to get a square wave
    filteredResult = [e for e in schmidtTrigger(result)]
    filteredResult2 = [e for e in schmidtTrigger(result2)]

    combinedResult = list(andGate(filteredResult, filteredResult2))
    combinedResult = list(schmidtTrigger(covResult))"""
    
    # systemWave: expected time signal for comparing
    systemWave = [0] * len(result)
    delay = (endT - startT - 10) / 2.0
    for i in range(0, len(result)):
        fictionT = startT + delay + periodCount / frequency * i
        fictionTsecond = int(fictionT)
        fictionTms = int(fictionT * 1000) % 1000
        if fictionTsecond % 60 == 0:
            if (
                fictionTsecond % 300 == 0 and\
                fictionTsecond < SIGNAL_MORSE_CODE_SPACE_SEC
            ):
                # mute when transmitting morse code
                v = 0
            else:
                # whole minute signal
                v = 1 if fictionTms <= SIGNAL_MINUTE_MS else 0
        else:
            if fictionTsecond % 10:
                # whole 10-sec signal
                v = 1 if fictionTms < SIGNAL_1SEC_MS else 0
            else:
                # one sec signal
                v = 1 if fictionTms < SIGNAL_10SEC_MS else 0
        systemWave[i] = v
    
    diffPeriodsFound = phaseDiff(sampleSignal, systemWave, expected=duration)
    if None == diffPeriodsFound: return (0, 0)
    return (
        diffPeriodsFound[0] * windowSizeAsPeriods / frequency,
        diffPeriodsFound[1]
    )


def measureLatency(queue, **kvargs):
    measurements = []
    while True:
        try:
            measurement = measureLatencyOnce()
            print("New measurement: %.1fms" % (measurement[0] * 1000))
            measurements.append(measurement)
        except Exception as e:
            print(e)
            measurements.append(None) 
            continue

        N = 4
        if len(measurements) < N:
            continue
        else:
            if len(measurements) > 2 * N:
                measurements = measurements[:-2*N]
            valids = [e for e in measurements if e != None]
            if len(valids) >= N:
                avg = sum([a * b for a,b in valids]) / sum([b for a,b in valids]) 
            else:
                continue

        print("Suggested fix: %.1fms" % (avg * 1000))
        try:
            queue.put_nowait(avg)
            measurements = []
        except:
            continue



if __name__ == "__main__":
    measureLatencyOnce(verbose=True, duration=3, windowSizeAsPeriods=5)
