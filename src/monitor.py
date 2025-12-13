import psutil
import subprocess
import os
import time
from typing import Optional, Tuple, List, Callable
from threading import Thread, Event

GPUtil = None
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


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
    
    def set_state_change_callback(self, callback: Callable[[bool], None]):
        self._on_state_change = callback
    
    def get_cpu_usage(self) -> float:
        return psutil.cpu_percent(interval=None)
    
    def get_gpu_usage(self) -> float:
        if not GPU_AVAILABLE:
            return 0.0
        
        if self.config.prefer_nvidia_smi and os.path.exists(self.config.nvidia_smi_path):
            return self._get_gpu_usage_nvidia_smi()
        
        return self._get_gpu_usage_gputil()
    
    def _get_gpu_usage_nvidia_smi(self) -> float:
        try:
            result = subprocess.run(
                [self.config.nvidia_smi_path, '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                usages = [float(line.strip()) for line in lines if line.strip()]
                return max(usages) if usages else 0.0
        except Exception:
            pass
        return self._get_gpu_usage_gputil()
    
    def _get_gpu_usage_gputil(self) -> float:
        if not GPU_AVAILABLE:
            return 0.0
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                return max(gpu.load * 100 for gpu in gpus)
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
