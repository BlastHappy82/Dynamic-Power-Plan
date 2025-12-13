# Dynamic Power Plan v1.0.0

Automatically switches Windows power plans based on CPU/GPU load.

## Features

- **Multi-GPU Support** - Monitors NVIDIA, AMD, and Intel GPUs simultaneously
- **Automatic Power Plan Switching** - Boosts performance when CPU/GPU usage exceeds thresholds
- **Game Detection** - Automatically triggers boost mode when specified games are running
- **Lian Li L-Connect Integration** - Switches fan profiles alongside power plans
- **System Tray Interface** - Easy access to status and settings from the taskbar
- **Configurable Thresholds** - Customize CPU/GPU usage triggers and hold times

## Installation

1. Extract the zip to a folder of your choice
2. Run `DynamicPowerPlan.exe`
3. Right-click the tray icon to access settings

## Bug Fixes

- Fixed "Start with Windows" not working for admin apps (now uses Task Scheduler instead of registry)

## Requirements

- Windows 10/11
- Administrator privileges (for power plan switching)
