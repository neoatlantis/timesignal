#!/usr/bin/env python3

from math import pi, sin, sqrt
import sounddevice as sd
import numpy
import time

from .constants import *
from .walsh_filter import WalshFilter
from .phase_diff import phaseDiff


def schmidtTrigger(values):
    riseThreshold = 0.6
    fallThreshold = 0.5
    v = 0
    for x in values:
        if v == 0 and x > riseThreshold:
            v = 1
        elif v == 1 and x < fallThreshold:
            v = 0
        yield v

##############################################################################

def measureLatencyOnce(
    samplerate=SAMPLERATE,
    duration=10,
    frequency=SIGNAL_FREQUENCY,
    dtype=DATATYPE,
    windowSizeAsPeriods=5
):

    period = int(SAMPLERATE/SIGNAL_FREQUENCY)
    halfperiod = int(period/2)
    periodCount = windowSizeAsPeriods 
    windowSize = period * periodCount

    walshFilter = WalshFilter(
        framesPerPeriod=period, # e.g. period of 1kHz signal, in frames
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

        result = []
        for i in range(0, len(sample)-1, windowSize):
            result.append(walshFilter.measure(
                [e[0] for e in sample[i:i+windowSize]]
            ))

    maxV, minV = max(result), min(result)
    result = [(e - minV) / (maxV - minV) for e in result]

    # Use schmidt trigger to get a square wave
    filteredResult = [e for e in schmidtTrigger(result)]
    
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
    
    diffPeriodsFound = phaseDiff(filteredResult, systemWave, expected=duration)
    if None == diffPeriodsFound: return (0, 1)
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

        print("Suggested fix: ", avg * 1000, "ms")
        try:
            queue.put_nowait(avg)
            measurements = []
        except:
            continue



if __name__ == "__main__":
    print("Measured latency: %.1fms" % (measureLatencyOnce() * 1e3))
