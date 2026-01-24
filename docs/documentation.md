# Terminal Multiplexer Documentation

## Overview
The Terminal Multiplexer is a Python library that allows you to run multiple terminal commands in separate panes within a single terminal window. It automatically manages the layout of these panes to optimize the use of available space.

## Installation
Install the package using PDM:
```bash
pdm install
```

## Quick Start
```python
from multiplexer import TerminalMultiplexer

# Create a multiplexer instance
mux = TerminalMultiplexer()

# Add commands to run in panes
mux.run_command('ls -la')
mux.run_command('top')

# Start the multiplexer
mux.start()

# Let it run for a while
import time
time.sleep(10)

# Stop the multiplexer
mux.stop()
```

## API Reference

### TerminalMultiplexer
The main class for managing the multiplexer.

#### Methods
- `__init__(terminal=None)`: Initialize the multiplexer. Optionally pass a blessed Terminal instance.
- `run_command(command)`: Run a command in a new pane.
- `start()`: Start displaying the panes and running commands.
- `stop()`: Stop all panes and the multiplexer.

### Pane
Represents an individual pane.

#### Attributes
- `command`: The command being run.
- `x, y`: Position of the pane.
- `width, height`: Size of the pane.

### LayoutManager
Manages the layout of panes.

#### Methods
- `update_layout(panes)`: Update the positions and sizes of panes.

## Layouts
The multiplexer supports different layouts based on the number of panes:
- 1 pane: Full screen
- 2 panes: Vertical split
- 3-4 panes: 2x2 grid
- 5+ panes: Vertical stack

## Examples
See the `examples/` directory for more detailed examples.

## Output Example
Here is a simplified example of what the multiplexer displays (titles show the command run in each pane):

```
+------------------------------+  +------------------------------+
|        ls -la                |  |        top                   |
| file1  file2  dir/ ...       |  | PID  USER   %CPU %MEM  CMD    |
| ...                          |  | 1234 alice  1.2  0.8  python |
+------------------------------+  +------------------------------+
```

When running in a capable terminal the panes use colored headers and subtle background borders instead of ASCII characters for a more polished look.

## Troubleshooting
- Ensure your terminal supports the required capabilities.
- Commands that require interactive input may not work properly in panes.