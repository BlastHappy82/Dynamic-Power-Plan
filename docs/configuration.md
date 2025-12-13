# Configuration Guide

This document explains all configuration options for Dynamic Power Plan.

## Config File Location

The application looks for `config.json` in the following order:

1. **Same folder as the app** (recommended for portability)
2. **AppData folder**: `%APPDATA%\DynamicPowerPlan\config.json`

You can also specify a custom path:
```bash
python main.py --config "C:\path\to\my-config.json"
```

## Full Configuration Reference

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
  "gpuSampler": {
    "preferNvidiaSMI": true,
    "nvidiaSmiPath": "C:\\Windows\\System32\\nvidia-smi.exe"
  },
  "lconnect": {
    "enableFanBoost": true,
    "serviceName": "LConnectService",
    "targetFile": "C:\\ProgramData\\Lian-Li\\L-Connect 3\\settings\\L-Connect-Service",
    "mbOnDir": ".\\MB_on",
    "mbOffDir": ".\\MB_off",
    "backupFile": ".\\backup\\lconnect_original_backup.bin"
  },
  "logging": {
    "logDir": ".\\logs",
    "verbosity": "info"
  }
}
```

## Section Details

### plans

Power plan names as they appear in Windows.

| Setting | Type | Description |
|---------|------|-------------|
| `normal` | string | Name of your everyday/balanced power plan |
| `boost` | string | Name of your high performance power plan |

**Finding your power plan names:**
```cmd
powercfg /list
```

### thresholds

Thresholds that control when to switch modes.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `cpuPercent` | integer | 70 | CPU usage percentage to trigger boost |
| `gpuPercent` | integer | 70 | GPU usage percentage to trigger boost |
| `promoteHoldSeconds` | integer | 5 | Seconds of high usage before boosting |
| `demoteHoldSeconds` | integer | 15 | Seconds of low usage before returning to normal |

**Why hold times matter:**
- Prevents switching during brief usage spikes
- `promoteHoldSeconds`: Lower = faster response, Higher = less sensitive
- `demoteHoldSeconds`: Higher = stays in boost longer after load ends

### sampling

Controls how often the system is checked.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `intervalMs` | integer | 1000 | Milliseconds between usage samples |

Lower values = more responsive but slightly higher CPU usage.

### games

Executables that immediately trigger boost mode.

| Setting | Type | Description |
|---------|------|-------------|
| `watch` | array | List of executable names (case-insensitive) |

**Finding executable names:**
1. Open Task Manager
2. Find the game in Processes
3. Right-click → Properties
4. Note the exact filename (e.g., `cod.exe`)

### gpuSampler

GPU monitoring configuration.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `preferNvidiaSMI` | boolean | true | Use nvidia-smi for GPU monitoring |
| `nvidiaSmiPath` | string | System32 path | Path to nvidia-smi.exe |

**GPU Monitoring Priority:**
1. nvidia-smi (more accurate, NVIDIA only)
2. GPUtil library (fallback)
3. 0% if neither available

### lconnect

Lian Li L-Connect fan control settings.

| Setting | Type | Description |
|---------|------|-------------|
| `enableFanBoost` | boolean | Enable/disable fan profile switching |
| `serviceName` | string | L-Connect Windows service name |
| `targetFile` | string | L-Connect settings file to overwrite |
| `mbOnDir` | string | Folder containing full-speed fan config |
| `mbOffDir` | string | Folder containing normal fan config |
| `backupFile` | string | Backup of original L-Connect settings |

**Path formats:**
- Relative: `.\\MB_on` (relative to app folder)
- Absolute: `C:\\Users\\Name\\Configs\\MB_on`
- Environment: `%USERPROFILE%\\Configs\\MB_on`

### logging

Application logging settings.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `logDir` | string | `.\\logs` | Directory for log files |
| `verbosity` | string | `info` | Log level: `debug` or `info` |

## Tips

### Tuning for Your System

1. **Lower thresholds (50-60%)** if you want boost mode to activate earlier
2. **Higher thresholds (80-90%)** if you want it only during heavy loads
3. **Shorter promoteHold (2-3s)** for faster response to games
4. **Longer demoteHold (30-60s)** if your usage fluctuates a lot

### Disable Fan Control

If you only want power plan switching without fan control:
```json
"lconnect": {
  "enableFanBoost": false
}
```

### Multiple Game Profiles

Add all your games to the watch list:
```json
"games": {
  "watch": [
    "game1.exe",
    "game2.exe",
    "blender.exe",
    "premiere.exe"
  ]
}
```
