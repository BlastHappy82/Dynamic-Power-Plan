# Architecture Overview

This document explains the architecture and design of Dynamic Power Plan.

## Module Overview

The application is organized into distinct modules with clear responsibilities:

```
main.py
   │
   ├── src/config.py      (Configuration)
   ├── src/monitor.py     (System Monitoring)
   ├── src/power_manager.py (Power Control)
   └── src/tray_app.py    (User Interface)
```

## Module Details

### main.py - Entry Point

The main entry point that:
- Parses command-line arguments (optional custom config path)
- Initializes the Config object
- Creates and runs the TrayApp

```python
# Usage
python main.py                    # Use default config location
python main.py --config my.json   # Use custom config file
```

### src/config.py - Configuration Management

Handles all configuration loading, saving, and access.

**Key Components:**

- `DEFAULT_CONFIG`: Fallback values if no config file exists
- `get_app_directory()`: Finds the app's location (works with PyInstaller)
- `Config` class: Main configuration interface

**Config File Search Order:**
1. Custom path (if provided via --config)
2. Same folder as the application (config.json)
3. AppData folder (%APPDATA%\DynamicPowerPlan\config.json)

**Path Resolution:**
- Relative paths (starting with `.`) are resolved from the app directory
- Environment variables (%USERPROFILE%, etc.) are expanded
- Absolute paths are used as-is

### src/monitor.py - System Monitoring

Monitors CPU, GPU, and running processes to determine when to switch modes.

**Key Components:**

- `SystemMonitor` class: Main monitoring interface
- Background thread for continuous monitoring
- State machine with hysteresis (hold timers)

**Monitoring Strategy:**

```
                    ┌─────────────────┐
                    │   Monitoring    │
                    │     Loop        │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
       ┌─────────────┐               ┌─────────────┐
       │ CPU Usage   │               │ GPU Usage   │
       │ (psutil)    │               │ (nvidia-smi │
       │             │               │  or GPUtil) │
       └──────┬──────┘               └──────┬──────┘
              │                             │
              └──────────────┬──────────────┘
                             ▼
                    ┌─────────────────┐
                    │  Check Games    │
                    │   Running?      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  State Machine  │
                    │  (with hold     │
                    │   timers)       │
                    └─────────────────┘
```

**Hold Timer Logic:**
- Prevents rapid switching from brief spikes
- Promote hold: Must exceed threshold for X seconds before boosting
- Demote hold: Must be below threshold for Y seconds before returning to normal

### src/power_manager.py - Power Control

Handles Windows power plan switching and L-Connect fan file management.

**Key Components:**

- `PowerManager` class: Main power control interface
- Power plan switching via `powercfg` command
- Fan configuration file copying

**Power Plan Switching:**
```
powercfg /list          # Find plan GUID by name
powercfg /setactive     # Switch to plan
```

**Fan File Management:**
```
MB_on/L-Connect-Service  ──copy──▶  L-Connect 3 settings folder
       (full speed)

MB_off/L-Connect-Service ──copy──▶  L-Connect 3 settings folder
       (normal)
```

### src/tray_app.py - User Interface

System tray icon and menu using pystray.

**Key Components:**

- `TrayApp` class: Main UI controller
- Icon management (normal/boost states)
- Menu creation and callbacks
- Windows registry for startup option

**Menu Structure:**
```
┌────────────────────────┐
│ CPU: 45% | GPU: 30%    │  (Status - disabled)
├────────────────────────┤
│ ○ High Performance     │  (Radio button)
│ ○ Everyday (Normal)    │  (Radio button)
│ ● Auto                 │  (Radio button - default)
├────────────────────────┤
│ ☐ Start with Windows   │  (Checkbox)
│ Open Config File       │
│ Open Config Folder     │
├────────────────────────┤
│ Exit                   │
└────────────────────────┘
```

## Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        Application Start                          │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│  Config.load()  ────────▶  TrayApp.init()  ────────▶  Monitor    │
│                                                        .start()   │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Main Event Loop                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Monitor Thread:                                             │ │
│  │    1. Sample CPU/GPU                                         │ │
│  │    2. Check games running                                    │ │
│  │    3. Evaluate state transition                              │ │
│  │    4. Trigger callback if state changes                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                 │                                 │
│                                 ▼                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  On State Change:                                            │ │
│  │    1. PowerManager.apply_boost_mode(boost)                   │ │
│  │       - Switch power plan                                    │ │
│  │       - Copy fan config file                                 │ │
│  │    2. TrayApp.update_icon()                                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Threading Model

- **Main Thread**: Runs pystray event loop (blocking)
- **Monitor Thread**: Background daemon thread for sampling

The monitor thread communicates state changes via callback, which runs on the monitor thread but updates are thread-safe due to pystray's design.

## Error Handling

- Config loading: Falls back to defaults if file is corrupt
- GPU monitoring: Multi-vendor support (NVIDIA, AMD, Intel) with automatic fallbacks
- Power plan: Logs errors but continues operation
- File copying: Logs errors, doesn't crash application
