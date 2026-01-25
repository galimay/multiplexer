#!/usr/bin/env python3
"""
Example usage of the Terminal Multiplexer.

This script demonstrates how to run multiple commands in panes.
"""

from multiplexer import TerminalMultiplexer, styles
import time
import signal
import sys

def signal_handler(sig, frame):
    print('Stopping multiplexer...')
    mux.stop()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    mux = TerminalMultiplexer()

    # Add some example commands
    mux.run_command('ping -t localhost -n 20')  # Continuous ping
    mux.run_command('python -c "import time; [print(f\'Pane 2: {i}\') or time.sleep(1) for i in range(10)]"')
    mux.run_command('echo "Hello from pane 3" && sleep 5')
    # mux.run_command('python')

    print("Starting multiplexer. Press Ctrl+C to stop.")
    mux.start()

    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mux.stop()