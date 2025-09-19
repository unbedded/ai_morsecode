"""Global application configuration with simplified naming."""

# Import everything to support: from morsecode.components import global
# Then use: global.CfgSection.GLOBAL, global.CfgKey.FREQUENCY

from .keys import CfgKey
from .sections import CfgSection

__all__ = [
    "CfgSection",
    "CfgKey",
]
