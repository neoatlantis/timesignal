#!/usr/bin/env python3

import threading
import queue

from .send_signal import sendSignal


latencyFixer = queue.Queue()

latencyFixer.put_nowait(0.025)

senderThread = threading.Thread(
    target=sendSignal,
    kwargs={"latency_fixer": latencyFixer}
)

senderThread.start()
