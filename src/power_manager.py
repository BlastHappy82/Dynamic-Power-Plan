import os
import shutil
import subprocess
import logging
import platform
import filecmp
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0


class PowerManager:
    def __init__(self, config):
        self.config = config
        self._current_plan: Optional[str] = None
        self._fan_state_verified = False
        self._setup_logging()
    
    def _setup_logging(self):
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / 'power_manager.log'
        
        level = logging.DEBUG if self.config.verbosity == 'debug' else logging.INFO
        
        handler = logging.FileHandler(log_file)
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.setLevel(level)
    
    def get_current_power_plan(self) -> Optional[str]:
        if os.name != 'nt':
            return None
        
        try:
            result = subprocess.run(
                ['powercfg', '/getactivescheme'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=SUBPROCESS_FLAGS
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if '(' in output and ')' in output:
                    name = output.split('(')[1].split(')')[0]
                    return name
        except Exception as e:
            logger.error(f"Error getting power plan: {e}")
        
        return None
    
    def set_power_plan(self, plan_name: str) -> bool:
        if os.name != 'nt':
            logger.info(f"[Simulated] Would set power plan to: {plan_name}")
            return True
        
        try:
            result = subprocess.run(
                ['powercfg', '/list'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=SUBPROCESS_FLAGS
            )
            
            plan_guid = None
            for line in result.stdout.split('\n'):
                if plan_name.lower() in line.lower():
                    parts = line.split()
                    for part in parts:
                        if len(part) == 36 and part.count('-') == 4:
                            plan_guid = part
                            break
                    if plan_guid:
                        break
            
            if not plan_guid:
                logger.error(f"Power plan '{plan_name}' not found")
                return False
            
            result = subprocess.run(
                ['powercfg', '/setactive', plan_guid],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=SUBPROCESS_FLAGS
            )
            
            if result.returncode == 0:
                logger.info(f"Set power plan to: {plan_name}")
                self._current_plan = plan_name
                return True
            else:
                logger.error(f"Failed to set power plan: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting power plan: {e}")
            return False
    
    def copy_fan_config(self, boost: bool) -> bool:
        if not self.config.enable_fan_boost:
            return True
        
        source_dir = self.config.mb_on_dir if boost else self.config.mb_off_dir
        target_file = self.config.lconnect_target_file
        
        if not source_dir or not target_file:
            logger.warning("L-Connect paths not configured")
            return False
        
        source_file = Path(source_dir) / 'L-Connect-Service'
        
        if not source_file.exists():
            logger.error(f"Source file not found: {source_file}")
            return False
        
        if os.name != 'nt':
            logger.info(f"[Simulated] Would copy {source_file} to {target_file}")
            return True
        
        try:
            target_path = Path(target_file)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source_file, target_path)
            logger.info(f"Copied fan config: {'MB_on' if boost else 'MB_off'} -> {target_file}")
            
            self._update_status_file(target_path.parent, boost)
            
            self._restart_lconnect_service()
            
            return True
            
        except Exception as e:
            logger.error(f"Error copying fan config: {e}")
            return False
    
    def _update_status_file(self, target_dir: Path, boost: bool):
        on_file = target_dir / 'on'
        off_file = target_dir / 'off'
        
        try:
            if boost:
                if off_file.exists():
                    off_file.unlink()
                on_file.touch()
                logger.info("Status file set to: on")
            else:
                if on_file.exists():
                    on_file.unlink()
                off_file.touch()
                logger.info("Status file set to: off")
        except Exception as e:
            logger.warning(f"Error updating status file: {e}")
    
    def verify_fan_state(self, is_boosted: bool) -> bool:
        if not self.config.enable_fan_boost:
            return True
        
        if self._fan_state_verified:
            return True
        
        target_file = self.config.lconnect_target_file
        if not target_file:
            return True
        
        target_path = Path(target_file)
        target_dir = target_path.parent
        on_file = target_dir / 'on'
        off_file = target_dir / 'off'
        
        has_on = on_file.exists()
        has_off = off_file.exists()
        
        if has_on and has_off:
            logger.warning("Both on/off status files found. Resolving by re-applying current desired state.")
            result = self.copy_fan_config(is_boosted)
            if result:
                self._fan_state_verified = True
            return result
        
        if not has_on and not has_off:
            actual_state = self._detect_actual_fan_state(target_path)
            if actual_state is None or actual_state != is_boosted:
                logger.info(f"No status files found. Applying desired fan state ({'boost' if is_boosted else 'normal'}).")
                result = self.copy_fan_config(is_boosted)
            else:
                self._update_status_file(target_dir, is_boosted)
                result = True
            if result:
                self._fan_state_verified = True
            return result
        
        if is_boosted and has_off and not has_on:
            logger.info("Fan state mismatch detected: should be boost but status is off. Re-applying fan config.")
            result = self.copy_fan_config(True)
            if result:
                self._fan_state_verified = True
            return result
        elif not is_boosted and has_on and not has_off:
            logger.info("Fan state mismatch detected: should be normal but status is on. Re-applying fan config.")
            result = self.copy_fan_config(False)
            if result:
                self._fan_state_verified = True
            return result
        
        self._fan_state_verified = True
        return True
    
    def _detect_actual_fan_state(self, target_path: Path) -> Optional[bool]:
        if not target_path.exists():
            return None
        
        try:
            on_source = Path(self.config.mb_on_dir) / 'L-Connect-Service' if self.config.mb_on_dir else None
            off_source = Path(self.config.mb_off_dir) / 'L-Connect-Service' if self.config.mb_off_dir else None
            
            if on_source and on_source.exists() and filecmp.cmp(str(target_path), str(on_source), shallow=False):
                return True
            if off_source and off_source.exists() and filecmp.cmp(str(target_path), str(off_source), shallow=False):
                return False
        except Exception as e:
            logger.debug(f"Could not compare fan config files: {e}")
        
        return None
    
    def reset_fan_verification(self):
        self._fan_state_verified = False
    
    def _restart_lconnect_service(self):
        service_name = self.config.lconnect_service_name
        if not service_name:
            return
        
        try:
            subprocess.run(
                ['net', 'stop', service_name],
                capture_output=True,
                timeout=10,
                creationflags=SUBPROCESS_FLAGS
            )
            
            subprocess.run(
                ['net', 'start', service_name],
                capture_output=True,
                timeout=10,
                creationflags=SUBPROCESS_FLAGS
            )
            
            logger.info(f"Restarted service: {service_name}")
        except Exception as e:
            logger.warning(f"Could not restart service {service_name}: {e}")
    
    def apply_boost_mode(self, boost: bool):
        plan_name = self.config.boost_plan if boost else self.config.normal_plan
        
        self.set_power_plan(plan_name)
        
        self.copy_fan_config(boost)
        
        mode = "BOOST" if boost else "NORMAL"
        logger.info(f"Applied {mode} mode")
    
    def backup_current_fan_config(self) -> bool:
        if not self.config.backup_file:
            return False
        
        target_file = self.config.lconnect_target_file
        backup_file = self.config.backup_file
        
        if not os.path.exists(target_file):
            return False
        
        try:
            backup_path = Path(backup_file)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_file, backup_path)
            logger.info(f"Backed up fan config to: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Error backing up fan config: {e}")
            return False
