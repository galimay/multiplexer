"""
Terminal Multiplexer Package

This package provides functionality to run terminal commands in separate panes,
automatically managing layout and space optimization.
"""

from . import styles
from .multiplexer import TerminalMultiplexer

__all__ = ["TerminalMultiplexer", "styles"]
