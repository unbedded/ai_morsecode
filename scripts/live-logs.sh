#!/bin/bash
# Live Morse Code Log Monitor - Development Tool
# Provides real-time colored log monitoring for debugging and performance analysis

# Colors for different log levels
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Log directories (check current directory first for development mode)
LOG_DIRS=(
    "."  # Current directory (development mode)
    "$HOME/.local/share/morsecode/logs"  # User directory (fallback)
)

# Function to display usage
usage() {
    echo "🔍 Morse Code Live Log Monitor"
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -f, --filter PATTERN    Filter logs by pattern (grep-compatible)"
    echo "  -e, --events            Show only event-related logs"
    echo "  -p, --performance       Show only performance/timing logs"
    echo "  -d, --debug             Show only debug level logs"
    echo "  -h, --help              Show this help"
    echo
    echo "Examples:"
    echo "  $0                      # Monitor all logs with color coding"
    echo "  $0 --events             # Monitor only FFT/event logs"
    echo "  $0 --filter 'ERROR|WARNING'  # Monitor only errors and warnings"
    echo "  $0 --performance        # Monitor performance metrics"
}

# Function to colorize log lines
colorize_log() {
    while read -r line; do
        if [[ $line =~ ERROR ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ $line =~ WARNING ]]; then
            echo -e "${YELLOW}$line${NC}"
        elif [[ $line =~ DEBUG ]]; then
            echo -e "${GRAY}$line${NC}"
        elif [[ $line =~ INFO ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ $line =~ (FFT|Publishing|event|magnitude) ]]; then
            echo -e "${CYAN}$line${NC}"
        elif [[ $line =~ (performance|timing|fps|buffer) ]]; then
            echo -e "${MAGENTA}$line${NC}"
        elif [[ $line =~ (Real-time|Braille|ASCII|graphics) ]]; then
            echo -e "${BLUE}$line${NC}"
        else
            echo -e "${WHITE}$line${NC}"
        fi
    done
}

# Function to find the latest log file
get_latest_log() {
    # Check each directory for log files
    for log_dir in "${LOG_DIRS[@]}"; do
        # Expand tilde in path
        expanded_dir="${log_dir/#\~/$HOME}"

        # Development mode: look for morsecode-latest.log first
        if [[ -f "$expanded_dir/morsecode-latest.log" ]]; then
            echo "$expanded_dir/morsecode-latest.log"
            return
        fi

        # Fallback: find newest timestamped log (production mode)
        latest=$(find "$expanded_dir" -name "morsecode-*.log" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
        if [[ -n "$latest" ]]; then
            echo "$latest"
            return
        fi
    done
}

# Parse command line arguments
FILTER=""
EVENTS_ONLY=false
PERFORMANCE_ONLY=false
DEBUG_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--filter)
            FILTER="$2"
            shift 2
            ;;
        -e|--events)
            EVENTS_ONLY=true
            shift
            ;;
        -p|--performance)
            PERFORMANCE_ONLY=true
            shift
            ;;
        -d|--debug)
            DEBUG_ONLY=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Find log directory and file
LATEST_LOG=$(get_latest_log)

if [[ -z "$LATEST_LOG" ]]; then
    echo -e "${RED}Error: No log files found${NC}"
    echo "Run the morse code decoder first to create logs."
    echo "Searched in:"
    for log_dir in "${LOG_DIRS[@]}"; do
        echo "  - $log_dir"
    done
    exit 1
fi

LOG_DIR=$(dirname "$LATEST_LOG")

# Display header
clear
echo -e "${WHITE}🔍 Morse Code Live Log Monitor${NC}"
echo -e "${GRAY}===========================================${NC}"
echo -e "${GREEN}📁 Log Directory: $LOG_DIR${NC}"
echo -e "${GREEN}📄 Monitoring: $(basename "$LATEST_LOG")${NC}"

# Set up filtering
TAIL_CMD="tail -f \"$LATEST_LOG\""
FILTER_CMD=""

if [[ $EVENTS_ONLY == true ]]; then
    FILTER_CMD="grep --line-buffered -E '(FFT|Publishing|event|magnitude|probability)'"
elif [[ $PERFORMANCE_ONLY == true ]]; then
    FILTER_CMD="grep --line-buffered -E '(performance|timing|fps|buffer|chunk|samples)'"
elif [[ $DEBUG_ONLY == true ]]; then
    FILTER_CMD="grep --line-buffered 'DEBUG'"
elif [[ -n "$FILTER" ]]; then
    FILTER_CMD="grep --line-buffered -E '$FILTER'"
fi

echo -e "${GRAY}===========================================${NC}"

# Start monitoring with appropriate filtering
if [[ -n "$FILTER_CMD" ]]; then
    eval "$TAIL_CMD" | eval "$FILTER_CMD" | colorize_log
else
    eval "$TAIL_CMD" | colorize_log
fi