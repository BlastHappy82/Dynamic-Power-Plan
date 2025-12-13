# Dynamic Power Plan

A Windows system tray application that automatically switches power plans and Lian Li fan configurations based on CPU/GPU usage or running applications.

## Features

- **Automatic Power Plan Switching**: Monitors CPU and GPU usage and switches between power plans when thresholds are exceeded
- **Multi-GPU Support**: Detects and monitors NVIDIA, AMD, and Intel GPUs automatically
- **Lian Li Fan Control**: Integrates with L-Connect 3 to switch fan profiles
- **Game Detection**: Watches for specific executables and triggers boost mode automatically
- **System Tray Interface**: Clean tray icon with right-click menu for manual control
- **Configurable Thresholds**: Customize CPU/GPU thresholds, hold times, and watched games
- **Start with Windows**: Option to run automatically at Windows startup
- **Admin Elevation**: Automatically requests admin rights for power plan changes

## Quick Start

### Option 1: Download Pre-built Release

1. Download the latest release from [GitHub Releases](../../releases)
2. Extract the ZIP to a folder of your choice (e.g., your Dropbox folder for portability)
3. Double-click `DynamicPowerPlan.exe`
4. Click "Yes" on the UAC prompt (admin rights required)
5. The tray icon appears - you're done!

### Option 2: Run from Source

1. Install Python 3.11+ from [python.org](https://python.org)
2. Clone or download this repository
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application (as Administrator):
   ```bash
   python main.py
   ```

## Configuration

Edit `config.json` to customize the application. The file is located in the same folder as the executable.

### Example Configuration

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
  "sampling": {
    "intervalMs": 1000
  },
  "games": {
    "watch": [
      "cod.exe",
      "bf2042.exe",
      "fortniteclient-win64-shipping.exe"
    ]
  },
  "gpu": {
    "nvidia": {
      "preferSMI": true,
      "smiPath": "C:\\Windows\\System32\\nvidia-smi.exe"
    },
    "amd": {
      "preferPyadl": true
    }
  },
  "lconnect": {
    "enableFanBoost": true,
    "serviceName": "LConnectService",
    "targetFile": "C:\\ProgramData\\Lian-Li\\L-Connect 3\\settings\\L-Connect-Service",
    "mbOnDir": ".\\MB_on",
    "mbOffDir": ".\\MB_off"
  }
}
```

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `plans.normal` | Name of your normal/everyday power plan | "Everyday" |
| `plans.boost` | Name of your high performance power plan | "High Performance" |
| `thresholds.cpuPercent` | CPU usage threshold to trigger boost mode | 70 |
| `thresholds.gpuPercent` | GPU usage threshold to trigger boost mode | 70 |
| `thresholds.promoteHoldSeconds` | Seconds of sustained high usage before switching to boost | 5 |
| `thresholds.demoteHoldSeconds` | Seconds of sustained low usage before switching back to normal | 15 |
| `sampling.intervalMs` | How often to check CPU/GPU usage (milliseconds) | 1000 |
| `games.watch` | List of executable names that trigger boost mode when running | [] |
| `gpu.nvidia.preferSMI` | Use nvidia-smi for NVIDIA GPU monitoring | true |
| `gpu.nvidia.smiPath` | Path to nvidia-smi.exe | System default |
| `gpu.amd.preferPyadl` | Use pyadl library for AMD GPU monitoring | true |
| `lconnect.enableFanBoost` | Enable Lian Li fan profile switching | true |

## System Tray Menu

Right-click the tray icon to access:

- **Status Display**: Current CPU/GPU usage and mode (Boost/Normal)
- **High Performance**: Manually switch to boost mode
- **Everyday (Normal)**: Manually switch to normal mode  
- **Auto**: Return to automatic switching based on usage
- **Start with Windows**: Toggle auto-start at Windows boot
- **Open Config File**: Edit configuration in your default editor
- **Exit**: Close the application

## How It Works

1. The app monitors CPU and GPU usage at regular intervals (default: 1 second)
2. When usage exceeds the threshold for the "promote hold time", it:
   - Switches to the "High Performance" power plan via `powercfg`
   - Copies the `MB_on` fan configuration to L-Connect 3 (full-speed fans)
3. When usage drops below the threshold for the "demote hold time", it:
   - Switches back to the "Everyday" power plan
   - Copies the `MB_off` fan configuration (normal fans)
4. If a watched game executable is detected running, boost mode is triggered immediately

## Requirements

- **Windows 10/11**
- **Administrator rights** (for power plan switching)
- **Lian Li L-Connect 3** (optional, for fan control features)

### GPU Monitoring Support

The application automatically detects and monitors GPUs from multiple vendors:

| GPU Vendor | Primary Method | Fallback Method |
|------------|----------------|-----------------|
| **NVIDIA** | nvidia-smi command | GPUtil library |
| **AMD** | pyadl library | Windows Performance Counters |
| **Intel** | Windows Performance Counters | - |

**Notes:**
- NVIDIA: Install the NVIDIA driver (nvidia-smi is included)
- AMD: Supported out of the box
- Intel: Works automatically on Windows 10/11
- Multi-GPU: Returns maximum utilization across all detected GPUs

### Power Plan Setup

The app expects power plans named "Everyday" and "High Performance" by default. To check your available power plans:

```cmd
powercfg /list
```

You can change the plan names in `config.json` to match your existing plans.

## Building from Source

To create a standalone executable:

1. Install Python 3.11+ and dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```
2. Build the executable:
   ```bash
   pyinstaller --clean DynamicPowerPlan.spec
   ```
3. Find the executable in the `dist` folder

## Project Structure

```
DynamicPowerPlan/
├── DynamicPowerPlan.exe  # Main executable
├── config.json           # User configuration
├── MB_on/                # Full-speed fan configuration
│   └── L-Connect-Service
├── MB_off/               # Normal fan configuration
│   └── L-Connect-Service
├── backup/               # Original L-Connect backup
└── logs/                 # Application logs
```

## Troubleshooting

### App doesn't start
- Make sure you're running as Administrator
- Check that Python dependencies are installed (if running from source)

### Power plan doesn't change
- Verify the power plan names in config.json match your system (`powercfg /list`)
- Ensure you clicked "Yes" on the UAC prompt

### GPU not detected
- NVIDIA: Install the latest NVIDIA driver
- AMD: Supported out of the box
- Check the logs folder for error messages

### L-Connect fan profiles not working
- Verify L-Connect 3 is installed
- Check the target path in config.json matches your L-Connect installation
- The MB_on and MB_off folders must contain valid L-Connect-Service files

## License

This project is open source. See LICENSE for details.

## Support

If you encounter issues, please [open an issue](../../issues) on GitHub.
