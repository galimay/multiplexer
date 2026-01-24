#!/usr/bin/env python3

from multiplexer import TerminalMultiplexer
import time

def main():
    mux = TerminalMultiplexer()
    mux.run_command('echo "Hello from pane 1"')
    mux.run_command('echo "Hello from pane 2"')
    mux.start()
    time.sleep(2)  # Run for 2 seconds
    mux.stop()

if __name__ == '__main__':
    main()