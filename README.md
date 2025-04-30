# CARLA Simulator Racing Demo Booth

This project is a CARLA-based driving simulation experience designed for a public demonstration booth. One vehicle is controlled by a human driver using the Logitech G29 steering wheel, while the other is autonomously driven using our custom algorithm.



## Demo Overview

- Map selection via Pygame UI
- Vehicle reset to initial positions on key press
- 5-second countdown before control starts
- Time tracking until goal is reached
- Dashboard-style GUI overlay
- Real-time HUD and top-left speed display
- High score leaderboard with name input (G29-only)
- Full integration with Logitech G29 (wheel, pedals, buttons)

## Features

| Feature                   | Description |
|--------------------------|-------------|
| **Map Selection**         | Choose CARLA maps through a Pygame interface |
| **Vehicle Reset**         | Return both vehicles to initial spawn points using `set_transform()` |
| **Countdown Start**       | 5-second countdown before user control is enabled |
| **Time Tracking**         | Measure elapsed time from start to goal |
| **HUD & Dashboard**       | Transparent semi-circular gauges for speed, rpm, etc. in bottom-left |
| **Top 10 Leaderboard**    | Record top times with 5-character name input via G29 |
| **G29 Wheel Control**     | All inputs handled through Logitech G29 (no keyboard) |

## Requirements
- Python 3.8+
- CARLA Simulator (0.9.15)
- pygame
- evdev (for Linux G29 support)
- numpy

## How to Run
# 1. Launch your CARLA simulator
./CarlaUE4.sh -RenderOffScreen

# 2. Run the main simulation script
python3 main.py

## Notes
- The autonomous vehicle logic is pre-implemented and does not require modification.
- All UI and control logic is designed around a dual-monitor setup, with the user view and HUD displayed separately.
- High scores are saved locally in .txt format with timestamps.

