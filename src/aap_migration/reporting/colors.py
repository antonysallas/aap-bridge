"""Color definitions for console output.

This module provides centralized color palette using Rich color names
for consistent visual styling across the migration tool's console output.
"""


class MigrationColors:
    """Centralized color palette for AAP Bridge console output.

    Uses Rich library color names for consistent, professional appearance.
    All colors are terminal-safe and work in both light and dark terminals.

    Reference: https://rich.readthedocs.io/en/stable/appendix/colors.html
    """

    # Semantic colors for messages
    INFO = "cyan"
    SUCCESS = "green"
    WARNING = "yellow"
    ERROR = "red"
    DEBUG = "dim"

    # Component-specific colors
    PROGRESS = "blue"
    PHASE = "magenta"
    METRIC = "light_steel_blue"
    SPINNER = "dark_slate_gray1"

    # Status colors
    RUNNING = "yellow"
    COMPLETE = "green"
    FAILED = "red"
    PENDING = "dim"
    SKIPPED = "dark_orange"

    # Data colors
    RESOURCE_COUNT = "bright_cyan"
    RATE = "bright_blue"
    TIME = "bright_magenta"

    # UI elements
    BORDER = "blue"
    HEADER = "bold bright_white"
    LABEL = "bold"
