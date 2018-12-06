#!/usr/bin/env python3

from math import pi, sin
import sounddevice as sd
import numpy
import time

def schmidtTrigger(values):
    riseThreshold = 0.5
    fallThreshold = 0.4
    v = 0
    for x in values:
        if v == 0 and x > riseThreshold:
            v = 1
        elif v == 1 and x < fallThreshold:
            v = 0
        yield v

def xorGate(array1, array2):
    assert len(array1) == len(array2)
    for i in range(0, len(array1)):
        yield 0 if array1[i] == array2[i] else 1

##############################################################################

#from morse_code import getMorseData

fs=48000
freq = 1000
period=int(fs/freq)
halfperiod=int(period/2)
dtype="float32"
periodCount = 5


with sd.InputStream(
    samplerate=fs,
    channels=2,
    dtype=dtype
) as stream:
    startT = time.time()
    sample, _ = stream.read(fs * 10)
    endT = time.time()

    walsh = numpy.array([
        (
            1 if int(i / halfperiod) % 2 else -1,
            0
        )
        for i in range(0, period * periodCount)
    ])
    result = []
    for i in range(0, len(sample)-1, len(walsh)):
        result.append(
            sum([e[0] for e in walsh * sample[i:i+len(walsh)]])
        )

maxV, minV = max(result), min(result)
result = [(e - minV) / (maxV - minV) for e in result]

averageV = sum(result) / len(result)
if averageV > 0.5:
    result = [1.0 - e for e in result] # reverse phase
    averageV = 1.0 - averageV
if averageV > 0.25:
    print("Bad sample: %f. Try again." % averageV)
    exit(1)


filteredResult = [e for e in schmidtTrigger(result)]
systemWave = [0] * len(result)

delay = (endT - startT - 10) / 2.0
for i in range(0, len(result)):
    fictionT = startT + delay + periodCount / freq * i
    fictionTsecond = int(fictionT)
    fictionTms = int(fictionT * 1000) % 1000

    if fictionTsecond % 300 == 0:
        v = 1 if fictionTms <= 500 else 0
    else:
        if fictionTsecond % 10:
            v = 1 if fictionTms < 80 else 0
        else:
            v = 1 if fictionTms < 160 else 0
    systemWave[i] = v

diffWave = [i for i in xorGate(systemWave, filteredResult)]

for i in range(0, len(result)):
    print(result[i], filteredResult[i], systemWave[i], diffWave[i])
