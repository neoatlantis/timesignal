#!/usr/bin/env python3

from math import pi, sin
import sounddevice as sd
import numpy
import time

from .constants import *
from .morse_code import getMorseData



def pullLatencyFix(latencyFixer):
    if not latencyFixer: return None
    try:
        fix = latencyFixer.get_nowait()
        #if not (-0.03 <= fix <= 0.03):
        #    return None
        return fix
    except:
        return None


def sendSignal(
    samplerate=SAMPLERATE,
    frequency=SIGNAL_FREQUENCY,
    dtype=DATATYPE,
    latency_fix=0,
    latency_fixer=None
):
    
    # 1. Prepare for signals

    signal_1_1ms = [(i, 0) for i in 
        [
            sin(i / ONE_MILLISECOND_FRAMES * 2 * pi) + 
            sin(i / ONE_MILLISECOND_FRAMES * 4 * pi)
            for i in range(0, ONE_MILLISECOND_FRAMES+1)
        ]
    ]
    signal_0_1ms = [(0, 0) for i in range(0, ONE_MILLISECOND_FRAMES+1)]

    # 2. Cache signals

    print("Caching signals...")
    signals = [
        [
            numpy.array([signal_type * ms][0], dtype=dtype)
            for ms in range(0, 1001)
        ]
        for signal_type in [signal_0_1ms, signal_1_1ms]
    ]


    nowtime = time.time()
    currentMinute = int(nowtime / 60) % 60
    morseCodePlayed = True 

    print("Start sending...")

    with sd.OutputStream(
        samplerate=samplerate,
        channels=2,
        latency="low",
        dtype=dtype
    ) as stream:

        def TimeGenerator():
            nonlocal latency_fix
            while True:
                nowtime = time.time() + latency_fix
                yield (
                    int(nowtime / 60) % 60,
                    int(nowtime) % 60,
                    int(nowtime * 1000) % 1000
                )
        timeGen = TimeGenerator()

        while True:
            minute, seconds, milliseconds = next(timeGen)

            duration = SIGNAL_1SEC_MS if seconds % 10 else SIGNAL_10SEC_MS
            if minute != currentMinute:
                duration = SIGNAL_MINUTE_MS 
                currentMinute = minute
                morseCodePlayed = False 

            if 1 <= seconds < SIGNAL_MORSE_CODE_SPACE_SEC and minute % 5 == 0:
                if not morseCodePlayed:
                    stream.write(0.5 * getMorseData(
                        samplerate, MORSE_CODE_FREQUENCY, dtype=dtype))
                    morseCodePlayed = True
                else:
                    continue
            else:
                if milliseconds >= duration: # silent period
                    if milliseconds < 750:
                        # fix latency at silence time
                        deltaFix = pullLatencyFix(latency_fixer)
                        if deltaFix != None:
                            latency_fix += deltaFix
                            if latency_fix > 0.1:
                                print("Latency > 100ms: Fix failed? Reset to zero.")
                                latency_fix = 0
                            print("Current latency: %dms" % (latency_fix*1e3))
                        milliseconds = next(timeGen)[2]
                    data = signals[0][1000-milliseconds]
                else:   # sending period
                    data = signals[1][duration-milliseconds]
                stream.write(data)
