#!/usr/bin/env python3

def xorGate(array1, array2):
    assert len(array1) == len(array2)
    for i in range(0, len(array1)):
        yield 0 if array1[i] == array2[i] else 1

def differentWindowFinder(diffWave):
    # Find slices[i:j] of all ones
    maxI = len(diffWave) - 1
    i, j = 1, 1
    while i < maxI:
        if diffWave[i]:
            j = i
            while j < maxI and diffWave[j]: j += 1
            yield (i, j)
            i = j + 1
        else:
            i += 1

def isRisingEdge(series):
    v = series[0]
    if series[-1] <= series[0]: return False
    for e in series:
        if e < v: return False
        v = e
    return True

def phaseDiff(inputWave, referenceWave, expected=10, maxLatencyInPeriods=10):
    outputs = []
    diffWave = [i for i in xorGate(referenceWave, inputWave)]
    print("\n")
    for i, j in differentWindowFinder(diffWave):
        if i < 1: continue

        if not isRisingEdge(referenceWave[i-1:j+1]):
            # not a rising edge in reference wave
            continue
        if not isRisingEdge(inputWave[i-1:j+1]): continue

        if sum(inputWave[i:j]) > sum(referenceWave[i:j]):
            latency = -(j-i) # input wave goes earlier than reference
        else:
            latency = (j-i)
        if abs(latency) > maxLatencyInPeriods: continue
        print(i, j, inputWave[i-1:j+1], referenceWave[i-1:j+1], "=>", latency)
        outputs.append(latency)

    if not outputs: 
        print("Phase diff failed.")
        return None
    return sum(outputs) / len(outputs), len(outputs) / expected
