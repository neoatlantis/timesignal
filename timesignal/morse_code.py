#!/usr/bin/env python3

import numpy
from datetime import datetime

morseCode =  {
    'A': '.-',     'B': '-...',   'C': '-.-.', 
    'D': '-..',    'E': '.',      'F': '..-.',
    'G': '--.',    'H': '....',   'I': '..',
    'J': '.---',   'K': '-.-',    'L': '.-..',
    'M': '--',     'N': '-.',     'O': '---',
    'P': '.--.',   'Q': '--.-',   'R': '.-.',
    'S': '...',    'T': '-',      'U': '..-',
    'V': '...-',   'W': '.--',    'X': '-..-',
    'Y': '-.--',   'Z': '--..',

    '0': '-----',  '1': '.----',  '2': '..---',
    '3': '...--',  '4': '....-',  '5': '.....',
    '6': '-....',  '7': '--...',  '8': '---..',
    '9': '----.' 
}

def getMorseData(samplerate, freq, dtype="float32"):
    now = datetime.utcnow()
    timestr = "%02d%02d%02d%02d" % (now.month, now.day, now.hour, now.minute)

    L = int(samplerate / freq / 2)
    waveletcount = lambda ms: int(ms / (1000 / freq))
    wavegen = lambda ms: ([(1, 1)] * L + [(-1, -1)] * L) * waveletcount(ms)
    nullgen = lambda ms: ([(0, 0)] * (2 * L)) * waveletcount(ms)

    output = []
    DOT_LENGTH = 54 
    for char in timestr:
        code = morseCode[char]
        for c in code:
            if output: output += nullgen(DOT_LENGTH)
            output += wavegen(DOT_LENGTH if c == "." else 3 * DOT_LENGTH)
        output += nullgen(3 * DOT_LENGTH)

#    print(len(output) / samplerate)
    return numpy.array(output[1:], dtype=dtype)


if __name__ == "__main__":
    import sounddevice as sd

    sd.default.samplerate = 48000
    sd.default.channels = 2
    sd.default.dtype = "float32" 

    data = getMorseData(48000, 500)
    print(len(data))
    sd.play(data, blocking=True)
    sd.stop()
