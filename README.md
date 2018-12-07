timesignal: An audio time pulse generator
=========================================

This library utilizes `sounddevice` as audio in- and output. It generates a
radio-time-service-alike signal on soundcard according to local system time.
The latency of soundcard is continously monitored via Fourier filtering,
and can be thus compensated. A measured latency <10ms should be achievable
when the audio volume is high enough.

Audio is generated on 3 frequencies: the signal frequency and morse code
frequency can be configured via `timesignal/constants.py` and are by default
1kHz and 600Hz respectively. The signal frequency is also sent doubled, so 2kHz
additionally.

The same time when audio is played on soundcard, another thread will record 
them periodically and compare the measured signal with system clock for
latency. Here the picked signal will be passed to Fourier filter, after which
2 amplitude-time waves at 1kHz and 2kHz are generated. These 2 signals will
determine the measured signal, which may have a latency(when uncompensated)
from 20ms on PC to >60ms with bluetooth speaker.

A morse code with month/day/hour/minute (8 characters) will be sent at each
5 minutes. During morse code, no time pulses will be generated for 10 seconds.

## Usage

`python3 -m timesignal` after you've cloned this git repo.
