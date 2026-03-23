#!/usr/bin/env python3
"""
Example usage of the Terminal Multiplexer.

This script demonstrates how to run multiple commands in panes.
"""

import asyncio
from multiplexer import TerminalMultiplexer, styles
import signal
import sys

async def main():
    mux = TerminalMultiplexer()

    # Add some example commands
    mux.run_command('ping localhost -n 10')
    mux.run_command('echo "Hello from pane 2" && sleep 2 && echo "Goodbye from pane 2"')
    mux.run_command('ls -la && sleep 2 && echo "Finished listing"')
    mux.run_command('python -u -c "import time; [print(i) or time.sleep(1) for i in range(5)]"')
    mux.run_command('python')

    print("Starting multiplexer. Press Ctrl+C to stop.")
    try:
        await mux.start()
    except KeyboardInterrupt:
        await mux.stop()

if __name__ == '__main__':
    asyncio.run(main())