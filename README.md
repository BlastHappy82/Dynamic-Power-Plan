# Dynamic Power Plan

A Windows system tray application that automatically switches power plans and Lian Li fan configurations based on CPU/GPU usage or running applications.

## Features

- **Automatic Power Plan Switching**: Monitors CPU and GPU usage and switches between "Everyday" and "High Performance" power plans when thresholds are exceeded
- **Lian Li Fan Control**: Automatically copies fan configuration files to L-Connect 3 to switch between normal and full-speed fan modes
- **Game Detection**: Watches for specific executables and triggers high performance mode when games are running
- **System Tray Interface**: Clean tray icon with right-click menu for manual control
- **Configurable Thresholds**: Customize CPU/GPU thresholds, hold times, and watched applications via JSON config
- **Start with Windows**: Option to run automatically at Windows startup

## Quick Start

### Option 1: Download Pre-built Release

1. Download the latest release from [GitHub Releases](../../releases)
2. Extract the ZIP to a folder of your choice
3. Double-click `DynamicPowerPlan.exe`
4. The tray icon appears - you're done!

### Option 2: Run from Source

1. Install Python 3.11+ from [python.org](https://python.org)
2. Clone or download this repository
3. Install dependencies:
   ```bash
   pip install pystray pillow psutil gputil
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Configuration

Edit `config.json` to customize the application:

```json
{
  "plans": {
    "normal": "Everyday",
    "boost": "High Performance"
  },
  "thresholds": {
    "cpuPercent": 70,
    "gpuPercent": 70,
    "promoteHoldSeconds": 5,
    "demoteHoldSeconds": 15
  },
  "games": {
    "watch": [
      "cod.exe",
      "bf2042.exe",
      "your-game.exe"
    ]
  }
}
```

### Configuration Options

| Setting | Description |
|---------|-------------|
| `plans.normal` | Name of your normal/everyday power plan |
| `plans.boost` | Name of your high performance power plan |
| `thresholds.cpuPercent` | CPU usage threshold to trigger boost mode |
| `thresholds.gpuPercent` | GPU usage threshold to trigger boost mode |
| `thresholds.promoteHoldSeconds` | Seconds of sustained high usage before switching to boost |
| `thresholds.demoteHoldSeconds` | Seconds of sustained low usage before switching back to normal |
| `games.watch` | List of executable names that trigger boost mode when running |

## System Tray Menu

Right-click the tray icon to access:

- **Status Display**: Current CPU/GPU usage and mode
- **High Performance**: Manually switch to boost mode
- **Everyday (Normal)**: Manually switch to normal mode  
- **Auto**: Return to automatic switching based on usage
- **Start with Windows**: Toggle auto-start at Windows boot
- **Open Config File**: Edit configuration in your default editor
- **Exit**: Close the application

## How It Works

1. The app monitors CPU and GPU usage at regular intervals
2. When usage exceeds the threshold for the hold time, it:
   - Switches to the "High Performance" power plan via `powercfg`
   - Copies the `MB_on` fan configuration to L-Connect 3 settings (full-speed fans)
3. When usage drops below the threshold for the demote hold time, it:
   - Switches back to the "Everyday" power plan
   - Copies the `MB_off` fan configuration (normal fans)
4. If a watched game executable is detected running, boost mode is triggered immediately

## Requirements

- Windows 10/11
- Lian Li L-Connect 3 (for fan control features)
- NVIDIA GPU with nvidia-smi (optional, for GPU monitoring)

## Building from Source

To create a standalone executable:

1. Install Python 3.11+ and dependencies
2. Run the build script:
   ```bash
   build.bat
   ```
3. Find the executable in the `dist` folder

## Project Structure

```
DynamicPowerPlan/
├── main.py              # Application entry point
├── config.json          # User configuration
├── src/
│   ├── config.py        # Configuration management
│   ├── monitor.py       # CPU/GPU monitoring
│   ├── power_manager.py # Power plan switching
│   └── tray_app.py      # System tray interface
├── MB_on/               # Full-speed fan configuration
├── MB_off/              # Normal fan configuration
├── Resources/           # Tray icons
└── docs/                # Documentation
```

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for guidelines.

## License

This project is open source. See LICENSE for details.

## Support

If you encounter issues, please [open an issue](../../issues) on GitHub.
