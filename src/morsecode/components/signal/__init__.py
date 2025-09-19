"""Signal processing component with unified config imports."""

# Export everything from config modules for easy importing
from .signal_config_keys import SignalCfgKey, SignalCfgSection
from .signal_config_schema import SignalConfigSchema, SignalMode
from .signal_processor import SignalProcessor

__all__ = [
    "SignalCfgKey",
    "SignalCfgSection",
    "SignalConfigSchema",
    "SignalMode",
    "SignalProcessor",
]
