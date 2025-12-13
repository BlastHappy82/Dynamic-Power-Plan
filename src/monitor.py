import psutil
import subprocess
import os
import time
import platform
from typing import Optional, Tuple, List, Callable
from threading import Thread, Event
from enum import Enum

GPUtil = None
GPUTIL_AVAILABLE = False
try:
    import GPUtil as _GPUtil
    GPUtil = _GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    pass

pyadl = None
PYADL_AVAILABLE = False
try:
    import pyadl as _pyadl
    pyadl = _pyadl
    PYADL_AVAILABLE = True
except ImportError:
    pass


class GPUVendor(Enum):
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    UNKNOWN = "unknown"


class SystemMonitor:
    def __init__(self, config):
        self.config = config
        self._stop_event = Event()
        self._monitor_thread: Optional[Thread] = None
        
        self._current_cpu = 0.0
        self._current_gpu = 0.0
        self._is_boosted = False
        self._manual_override = False
        
        self._promote_start_time: Optional[float] = None
        self._demote_start_time: Optional[float] = None
        
        self._on_state_change: Optional[Callable[[bool], None]] = None
        
        self._detected_gpus: List[Tuple[GPUVendor, str]] = []
        self._detect_gpus()
    
    def _detect_gpus(self):
        self._detected_gpus = []
        
        if self._check_nvidia_available():
            self._detected_gpus.append((GPUVendor.NVIDIA, "NVIDIA GPU"))
        
        if self._check_amd_available():
            self._detected_gpus.append((GPUVendor.AMD, "AMD GPU"))
        
        if self._check_intel_available():
            self._detected_gpus.append((GPUVendor.INTEL, "Intel GPU"))
    
    def _check_nvidia_available(self) -> bool:
        if os.path.exists(self.config.nvidia_smi_path):
            try:
                result = subprocess.run(
                    [self.config.nvidia_smi_path, '--query-gpu=name', '--format=csv,noheader'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    return True
            except Exception:
                pass
        
        if GPUTIL_AVAILABLE and GPUtil is not None:
            try:
                gpus = GPUtil.getGPUs()
                return len(gpus) > 0
            except Exception:
                pass
        
        return False
    
    def _check_amd_available(self) -> bool:
        if PYADL_AVAILABLE and pyadl is not None:
            try:
                devices = pyadl.ADLManager.getInstance().getDevices()
                return len(devices) > 0
            except Exception:
                pass
        
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ['powershell', '-Command', 
                     "Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like '*AMD*' -or $_.Name -like '*Radeon*' } | Select-Object -First 1 Name"],
                    capture_output=True, text=True, timeout=5
                )
                return result.returncode == 0 and ('AMD' in result.stdout or 'Radeon' in result.stdout)
            except Exception:
                pass
        
        return False
    
    def _check_intel_available(self) -> bool:
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ['powershell', '-Command', 
                     "Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like '*Intel*' } | Select-Object -First 1 Name"],
                    capture_output=True, text=True, timeout=5
                )
                return result.returncode == 0 and 'Intel' in result.stdout
            except Exception:
                pass
        
        return False
    
    def get_detected_gpus(self) -> List[Tuple[GPUVendor, str]]:
        return self._detected_gpus.copy()
    
    def set_state_change_callback(self, callback: Callable[[bool], None]):
        self._on_state_change = callback
    
    def get_cpu_usage(self) -> float:
        return psutil.cpu_percent(interval=None)
    
    def get_gpu_usage(self) -> float:
        max_usage = 0.0
        
        for vendor, _ in self._detected_gpus:
            try:
                if vendor == GPUVendor.NVIDIA:
                    usage = self._get_nvidia_usage()
                elif vendor == GPUVendor.AMD:
                    usage = self._get_amd_usage()
                elif vendor == GPUVendor.INTEL:
                    usage = self._get_intel_usage()
                else:
                    usage = 0.0
                
                max_usage = max(max_usage, usage)
            except Exception:
                pass
        
        return max_usage
    
    def _get_nvidia_usage(self) -> float:
        if self.config.prefer_nvidia_smi and os.path.exists(self.config.nvidia_smi_path):
            try:
                result = subprocess.run(
                    [self.config.nvidia_smi_path, '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    usages = [float(line.strip()) for line in lines if line.strip()]
                    if usages:
                        return max(usages)
            except Exception:
                pass
        
        if GPUTIL_AVAILABLE and GPUtil is not None:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return max(gpu.load * 100 for gpu in gpus)
            except Exception:
                pass
        
        return 0.0
    
    def _get_amd_usage(self) -> float:
        if self.config.prefer_amd_pyadl and PYADL_AVAILABLE and pyadl is not None:
            try:
                devices = pyadl.ADLManager.getInstance().getDevices()
                if devices:
                    usages = []
                    for device in devices:
                        try:
                            usage = device.getCurrentUsage()
                            if usage is not None and usage >= 0:
                                usages.append(float(usage))
                        except AttributeError:
                            try:
                                activity = device.getCurrentActivity()
                                if activity is not None and hasattr(activity, 'iActivityPercent'):
                                    usages.append(float(activity.iActivityPercent))
                            except Exception:
                                pass
                        except Exception:
                            pass
                    if usages:
                        return max(usages)
            except Exception:
                pass
        
        return self._get_windows_gpu_usage_by_luid("AMD", "Radeon")
    
    def _get_intel_usage(self) -> float:
        return self._get_windows_gpu_usage_by_luid("Intel")
    
    def _get_windows_gpu_usage_by_luid(self, *vendor_keywords: str) -> float:
        if platform.system() != "Windows":
            return 0.0
        
        try:
            keywords_ps = " -or ".join([f"$_.Name -like '*{kw}*'" for kw in vendor_keywords])
            ps_script = f"""
try {{
    $adapters = Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | Where-Object {{ {keywords_ps} }}
    if (-not $adapters) {{ Write-Output 0; exit }}
    
    $samples = (Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction SilentlyContinue).CounterSamples
    if ($samples) {{
        $maxUsage = 0
        foreach ($sample in $samples) {{
            if ($sample.InstanceName -like '*engtype_3D*') {{
                if ($sample.CookedValue -gt $maxUsage) {{
                    $maxUsage = $sample.CookedValue
                }}
            }}
        }}
        Write-Output $maxUsage
    }} else {{
        Write-Output 0
    }}
}} catch {{
    Write-Output 0
}}
"""
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    val = float(result.stdout.strip().split('\n')[-1])
                    return max(0.0, val)
                except ValueError:
                    pass
        except Exception:
            pass
        
        return 0.0
    
    def get_running_processes(self) -> List[str]:
        processes = []
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name:
                    processes.append(name.lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes
    
    def is_watched_game_running(self) -> bool:
        running = self.get_running_processes()
        watched = self.config.watched_games
        return any(game in running for game in watched)
    
    def should_boost(self) -> Tuple[bool, str]:
        if self._manual_override:
            return self._is_boosted, "Manual override"
        
        if self.is_watched_game_running():
            return True, "Watched game detected"
        
        if self._current_cpu >= self.config.cpu_threshold:
            return True, f"CPU at {self._current_cpu:.1f}%"
        
        if self._current_gpu >= self.config.gpu_threshold:
            return True, f"GPU at {self._current_gpu:.1f}%"
        
        return False, "Normal usage"
    
    def _check_state_transition(self):
        should_boost, reason = self.should_boost()
        current_time = time.time()
        
        if self._manual_override:
            return
        
        if should_boost and not self._is_boosted:
            if self._promote_start_time is None:
                self._promote_start_time = current_time
            
            elapsed = current_time - self._promote_start_time
            if elapsed >= self.config.promote_hold_seconds:
                self._is_boosted = True
                self._promote_start_time = None
                self._demote_start_time = None
                if self._on_state_change:
                    self._on_state_change(True)
        
        elif not should_boost and self._is_boosted:
            if self._demote_start_time is None:
                self._demote_start_time = current_time
            
            elapsed = current_time - self._demote_start_time
            if elapsed >= self.config.demote_hold_seconds:
                self._is_boosted = False
                self._demote_start_time = None
                self._promote_start_time = None
                if self._on_state_change:
                    self._on_state_change(False)
        
        else:
            if should_boost:
                self._demote_start_time = None
            else:
                self._promote_start_time = None
    
    def _monitor_loop(self):
        psutil.cpu_percent(interval=None)
        
        while not self._stop_event.is_set():
            self._current_cpu = self.get_cpu_usage()
            self._current_gpu = self.get_gpu_usage()
            
            self._check_state_transition()
            
            self._stop_event.wait(self.config.sampling_interval_ms / 1000.0)
    
    def start(self):
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            return
        
        self._stop_event.clear()
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop(self):
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
    
    def set_manual_boost(self, boost: bool):
        self._manual_override = True
        if self._is_boosted != boost:
            self._is_boosted = boost
            if self._on_state_change:
                self._on_state_change(boost)
    
    def clear_manual_override(self):
        self._manual_override = False
        self._promote_start_time = None
        self._demote_start_time = None
    
    @property
    def current_cpu(self) -> float:
        return self._current_cpu
    
    @property
    def current_gpu(self) -> float:
        return self._current_gpu
    
    @property
    def is_boosted(self) -> bool:
        return self._is_boosted
    
    @property
    def is_manual_override(self) -> bool:
        return self._manual_override
