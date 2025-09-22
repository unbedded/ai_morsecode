# Development Scripts

## 🔍 Live Log Monitor (`live-logs.sh`)

Real-time colored log monitoring for development and debugging.

### Usage

```bash
# Basic monitoring with color coding
./scripts/live-logs.sh

# Monitor only events (FFT, magnitude, probability)
./scripts/live-logs.sh --events

# Monitor only performance metrics
./scripts/live-logs.sh --performance

# Filter by pattern
./scripts/live-logs.sh --filter "ERROR|WARNING"

# Monitor only debug logs
./scripts/live-logs.sh --debug
```

### Recommended Workflow

**Terminal 1: Run the app**
```bash
python -m morsecode.cli.main --dbg-graphics --opt-realtime audio.wav
```

**Terminal 2: Monitor logs**
```bash
./scripts/live-logs.sh --events
```

### Color Coding

- 🔴 **Red**: ERROR messages
- 🟡 **Yellow**: WARNING messages
- 🟢 **Green**: INFO messages
- ⚪ **Gray**: DEBUG messages
- 🔵 **Cyan**: Events (FFT, Publishing, magnitude)
- 🟣 **Magenta**: Performance (timing, fps, buffer)
- 🔵 **Blue**: Graphics (Real-time, Braille, ASCII)

## Development vs Production Logging

**Current (Development)**: Single log file `morsecode-latest.log` for easy monitoring

**Production Mode**: Uncomment timestamped logging in `src/morsecode/cli/main.py`:
```python
# Search for TODO: Production vs Development log naming
```

This switches to `morsecode-YYYYMMDD-HHMMSS.log` with automatic rotation.