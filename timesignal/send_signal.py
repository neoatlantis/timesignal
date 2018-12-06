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
        if not (0 <= fix <= 0.5):
            return None # accept only fix between 0-500ms
        print("New latency: %.1f ms" % (fix * 1000))
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
            sin(i / ONE_MILLISECOND_FRAMES * 2 * pi)
            for i in range(0, ONE_MILLISECOND_FRAMES)
        ]
    ]
    signal_0_1ms = [(0, 0) for i in range(0, ONE_MILLISECOND_FRAMES)]

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

    with sd.RawOutputStream(
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

            duration = 80 if seconds % 10 else 160
            if minute != currentMinute:
                duration = 500
                currentMinute = minute
                morseCodePlayed = False 

            if 1 <= seconds < 10 and minute % 5 == 0:
                if not morseCodePlayed:
                    stream.write(0.5 * getMorseData(samplerate, 600, dtype=dtype))
                    morseCodePlayed = True
                else:
                    continue
            else:
                if milliseconds >= duration: # silent period
                    if milliseconds < 750:
                        # fix latency at silence time
                        newFix = pullLatencyFix(latency_fixer)
                        if newFix != None:
                            latency_fix = newFix
                        milliseconds = next(timeGen)[2]
                    data = signals[0][1000-milliseconds]
                else:   # sending period
                    data = signals[1][duration-milliseconds]
                stream.write(data)
