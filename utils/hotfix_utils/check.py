"""An enumeration of the possible results of a check."""
from enum import (
    Enum,
)


class CHECK(Enum):
    """An enumeration of the possible results of a check."""

    UNDETERMINABLE = 0
    TRUE = 1
    FALSE = 2
