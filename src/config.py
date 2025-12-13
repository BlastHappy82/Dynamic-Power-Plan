import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

DEFAULT_CONFIG = {
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
            "preferSMI": True,
            "smiPath": "C:\\Windows\\System32\\nvidia-smi.exe"
        },
        "amd": {
            "preferPyadl": True
        }
    },
    "lconnect": {
        "enableFanBoost": True,
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


def get_app_directory() -> Path:
    """Get the directory where the application is located."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent


class Config:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            self.config_path = self._get_default_config_path()
        else:
            self.config_path = Path(config_path)
        
        self._config = self._load_config()
    
    def _get_default_config_path(self) -> Path:
        app_dir = get_app_directory()
        local_config = app_dir / 'config.json'
        if local_config.exists():
            return local_config
        
        if os.name == 'nt':
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            config_dir = Path(app_data) / 'DynamicPowerPlan'
        else:
            config_dir = Path.home() / '.config' / 'dynamic-power-plan'
        
        appdata_config = config_dir / 'config.json'
        if appdata_config.exists():
            return appdata_config
        
        return local_config
    
    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    return self._merge_config(DEFAULT_CONFIG, loaded)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                return DEFAULT_CONFIG.copy()
        else:
            self._save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    
    def _merge_config(self, default: Dict, loaded: Dict) -> Dict:
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_config(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = self._config
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def save(self):
        self._save_config()
    
    @property
    def normal_plan(self) -> str:
        return self._config['plans']['normal']
    
    @property
    def boost_plan(self) -> str:
        return self._config['plans']['boost']
    
    @property
    def cpu_threshold(self) -> int:
        return self._config['thresholds']['cpuPercent']
    
    @property
    def gpu_threshold(self) -> int:
        return self._config['thresholds']['gpuPercent']
    
    @property
    def promote_hold_seconds(self) -> int:
        return self._config['thresholds']['promoteHoldSeconds']
    
    @property
    def demote_hold_seconds(self) -> int:
        return self._config['thresholds']['demoteHoldSeconds']
    
    @property
    def sampling_interval_ms(self) -> int:
        return self._config['sampling']['intervalMs']
    
    @property
    def watched_games(self) -> List[str]:
        return [g.lower() for g in self._config['games']['watch']]
    
    @property
    def prefer_nvidia_smi(self) -> bool:
        if 'gpuSampler' in self._config and 'preferNvidiaSMI' in self._config['gpuSampler']:
            return self._config['gpuSampler']['preferNvidiaSMI']
        if 'gpu' in self._config and 'nvidia' in self._config['gpu']:
            return self._config['gpu']['nvidia'].get('preferSMI', True)
        return True
    
    @property
    def nvidia_smi_path(self) -> str:
        if 'gpuSampler' in self._config and 'nvidiaSmiPath' in self._config['gpuSampler']:
            return self._config['gpuSampler']['nvidiaSmiPath']
        if 'gpu' in self._config and 'nvidia' in self._config['gpu']:
            return self._config['gpu']['nvidia'].get('smiPath', 'C:\\Windows\\System32\\nvidia-smi.exe')
        return 'C:\\Windows\\System32\\nvidia-smi.exe'
    
    @property
    def prefer_amd_pyadl(self) -> bool:
        if 'gpu' in self._config and 'amd' in self._config['gpu']:
            return self._config['gpu']['amd'].get('preferPyadl', True)
        return True
    
    @property
    def enable_fan_boost(self) -> bool:
        return self._config['lconnect']['enableFanBoost']
    
    @property
    def lconnect_service_name(self) -> str:
        return self._config['lconnect']['serviceName']
    
    @property
    def lconnect_target_file(self) -> str:
        return os.path.expandvars(self._config['lconnect']['targetFile'])
    
    @property
    def mb_on_dir(self) -> str:
        path = os.path.expandvars(self._config['lconnect']['mbOnDir'])
        if path.startswith('.'):
            return str(get_app_directory() / path)
        return path
    
    @property
    def mb_off_dir(self) -> str:
        path = os.path.expandvars(self._config['lconnect']['mbOffDir'])
        if path.startswith('.'):
            return str(get_app_directory() / path)
        return path
    
    @property
    def backup_file(self) -> str:
        path = os.path.expandvars(self._config['lconnect']['backupFile'])
        if path.startswith('.'):
            return str(get_app_directory() / path)
        return path
    
    @property
    def log_dir(self) -> str:
        log_dir = self._config['logging']['logDir']
        if log_dir:
            path = os.path.expandvars(log_dir)
            if path.startswith('.'):
                return str(get_app_directory() / path)
            return path
        return str(self.config_path.parent / 'logs')
    
    @property
    def verbosity(self) -> str:
        return self._config['logging']['verbosity']
    
    def get_config_dir(self) -> Path:
        return self.config_path.parent
    
    def open_config_file(self):
        import subprocess
        if os.name == 'nt':
            os.startfile(str(self.config_path))
        else:
            subprocess.run(['xdg-open', str(self.config_path)])
