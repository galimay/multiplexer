# Terminal Multiplexer

## Description
This package provides a terminal multiplexer that allows users to run terminal commands in separate panes. The multiplexer automatically chooses the layout and location of these panes to optimize the terminal space.

## Installation
To install the package, use PDM:
```bash
pdm install
```

## Usage
Here is a simple example of how to use the terminal multiplexer:

```python
from multiplexer import TerminalMultiplexer

# Create an instance of the multiplexer
mux = TerminalMultiplexer()

# Run a command in a new pane
mux.run_command('ls')

# Start the multiplexer
mux.start()

# Stop when done
mux.stop()
```

For more detailed examples, see the `examples/` directory.

## Features
- Automatic pane management
- Dynamic layout adjustment based on terminal size
- Support for multiple commands running simultaneously
- Easy-to-use Python API

## Documentation
See the `docs/` directory for full documentation.

## Testing
Run tests with:
```bash
pdm run pytest
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.