#!/usr/bin/env python3
"""How matplotlib handles real-time data - comparison with our approach."""

from collections import deque

import matplotlib.pyplot as plt
import numpy as np

# Matplotlib's typical approaches:


def matplotlib_index_based():
    """Most common: Index-based plotting (no timestamps)."""
    # Data just arrives, gets appended, plotted against indices
    buffer = deque(maxlen=100)

    for i in range(150):  # Simulate data arrival
        value = np.sin(i * 0.1)
        buffer.append(value)

    # Plot against indices - no timestamps!
    plt.plot(list(buffer))
    plt.title("Matplotlib Index-Based (Most Common)")
    plt.xlabel("Sample Number")
    plt.ylabel("Value")
    plt.show()


def matplotlib_time_based():
    """Time-based: YOU provide the time array."""
    # You create your own consistent time axis
    sample_rate = 50.0  # Hz
    duration = 3.0  # seconds

    # YOUR responsibility to create consistent time
    t = np.linspace(0, duration, int(sample_rate * duration))
    y = np.sin(2 * np.pi * 1.0 * t)  # 1 Hz signal

    # Matplotlib just plots what you give it
    plt.plot(t, y)
    plt.title("Matplotlib Time-Based (YOU create time axis)")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Value")
    plt.show()


def matplotlib_realtime_animation():
    """Real-time: matplotlib.animation with timer."""
    # Matplotlib doesn't handle timestamps - it just calls your update function
    # at regular intervals (e.g. every 50ms)
    # YOU handle data buffering and time management

    buffer = deque(maxlen=100)

    def update_plot(frame):
        # Called every 50ms by matplotlib timer
        # Frame number is just a counter (0, 1, 2, 3...)
        value = np.sin(frame * 0.1)
        buffer.append(value)

        # Plot against sample indices (again, no timestamps!)
        ax.clear()
        ax.plot(list(buffer))

    # matplotlib just provides the timer - YOU handle everything else
    fig, ax = plt.subplots()
    # animation.FuncAnimation(fig, update_plot, interval=50)  # 50ms timer


if __name__ == "__main__":
    print("Matplotlib approaches:")
    print("1. Index-based (most common) - no timestamps at all")
    print("2. Time-based - YOU create the time axis")
    print("3. Real-time - matplotlib provides timer, YOU handle data")
    print()
    print("Key insight: Matplotlib rarely handles timestamps automatically!")
    print("The application is responsible for time management.")
