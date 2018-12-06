#!/usr/bin/env python3

import threading
import queue

from .send_signal import sendSignal
from .measure_latency import measureLatency


latencyFixer = queue.Queue()

senderThread = threading.Thread(
    target=sendSignal,
    kwargs={"latency_fixer": latencyFixer}
)
measureThread = threading.Thread(
    target=measureLatency,
    args=(latencyFixer,)
)

senderThread.start()

measureThread.start()
