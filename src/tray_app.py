import os
import subprocess
import sys
from pathlib import Path
from threading import Thread
from typing import Optional

import pystray
from PIL import Image, ImageDraw

from .config import Config
from .monitor import SystemMonitor
from .power_manager import PowerManager


def create_icon_image(color: str, size: int = 64) -> Image.Image:
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    if color == 'green':
        fill_color = (76, 175, 80, 255)
        outline_color = (56, 142, 60, 255)
    else:
        fill_color = (244, 67, 54, 255)
        outline_color = (211, 47, 47, 255)
    
    padding = 4
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=fill_color,
        outline=outline_color,
        width=2
    )
    
    center = size // 2
    if color == 'green':
        draw.polygon(
            [(center - 8, center + 4), (center - 2, center + 10), (center + 12, center - 8)],
            fill=(255, 255, 255, 255)
        )
    else:
        draw.polygon(
            [(center, center - 12), (center - 10, center + 8), (center + 10, center + 8)],
            fill=(255, 255, 255, 255)
        )
    
    return image


def load_icon_image(icon_path: str, fallback_color: str) -> Image.Image:
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path)
        except Exception:
            pass
    return create_icon_image(fallback_color)


class TrayApp:
    def __init__(self, config: Config):
        self.config = config
        self.monitor = SystemMonitor(config)
        self.power_manager = PowerManager(config)
        
        self._icon: Optional[pystray.Icon] = None
        self._running = False
        
        resources_dir = Path(__file__).parent.parent / 'Resources'
        self._icon_normal = load_icon_image(str(resources_dir / 'tray_normal.ico'), 'green')
        self._icon_boost = load_icon_image(str(resources_dir / 'tray_boost.ico'), 'red')
        
        self.monitor.set_state_change_callback(self._on_state_change)
    
    def _on_state_change(self, boost: bool):
        self.power_manager.apply_boost_mode(boost)
        self._update_icon()
    
    def _update_icon(self):
        if self._icon:
            if self.monitor.is_boosted:
                self._icon.icon = self._icon_boost
                self._icon.title = "Dynamic Power Plan - BOOST MODE"
            else:
                self._icon.icon = self._icon_normal
                self._icon.title = "Dynamic Power Plan - Normal"
    
    def _get_status_text(self, item) -> str:
        cpu = self.monitor.current_cpu
        gpu = self.monitor.current_gpu
        mode = "BOOST" if self.monitor.is_boosted else "Normal"
        override = " (Manual)" if self.monitor.is_manual_override else ""
        return f"CPU: {cpu:.1f}% | GPU: {gpu:.1f}% | {mode}{override}"
    
    def _set_boost_mode(self, icon, item):
        self.monitor.set_manual_boost(True)
        self._update_icon()
    
    def _set_normal_mode(self, icon, item):
        self.monitor.set_manual_boost(False)
        self._update_icon()
    
    def _set_auto_mode(self, icon, item):
        self.monitor.clear_manual_override()
    
    def _is_boost_checked(self, item) -> bool:
        return self.monitor.is_boosted and self.monitor.is_manual_override
    
    def _is_normal_checked(self, item) -> bool:
        return not self.monitor.is_boosted and self.monitor.is_manual_override
    
    def _is_auto_checked(self, item) -> bool:
        return not self.monitor.is_manual_override
    
    def _open_config(self, icon, item):
        self.config.open_config_file()
    
    def _open_config_folder(self, icon, item):
        config_dir = self.config.get_config_dir()
        if os.name == 'nt':
            os.startfile(str(config_dir))
        else:
            import subprocess
            subprocess.run(['xdg-open', str(config_dir)])
    
    def _toggle_startup(self, icon, item):
        if self._is_startup_enabled():
            self._disable_startup()
        else:
            self._enable_startup()
    
    def _is_startup_enabled(self) -> bool:
        if os.name != 'nt':
            return False
        
        try:
            result = subprocess.run(
                ['schtasks', '/query', '/tn', 'DynamicPowerPlan'],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _enable_startup(self):
        if os.name != 'nt':
            return
        
        try:
            if hasattr(sys, 'frozen'):
                task_command = f'"{sys.executable}"'
            else:
                task_command = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
            
            self._disable_startup()
            
            subprocess.run(
                [
                    'schtasks', '/create',
                    '/tn', 'DynamicPowerPlan',
                    '/tr', task_command,
                    '/sc', 'onlogon',
                    '/rl', 'highest',
                    '/f'
                ],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            print(f"Error enabling startup: {e}")
    
    def _disable_startup(self):
        if os.name != 'nt':
            return
        
        try:
            subprocess.run(
                ['schtasks', '/delete', '/tn', 'DynamicPowerPlan', '/f'],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception:
            pass
    
    def _quit(self, icon, item):
        self._running = False
        self.monitor.stop()
        icon.stop()
    
    def _create_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                self._get_status_text,
                None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "High Performance",
                self._set_boost_mode,
                checked=self._is_boost_checked,
                radio=True
            ),
            pystray.MenuItem(
                "Everyday (Normal)",
                self._set_normal_mode,
                checked=self._is_normal_checked,
                radio=True
            ),
            pystray.MenuItem(
                "Auto",
                self._set_auto_mode,
                checked=self._is_auto_checked,
                radio=True
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Start with Windows",
                self._toggle_startup,
                checked=lambda item: self._is_startup_enabled()
            ),
            pystray.MenuItem(
                "Open Config File",
                self._open_config
            ),
            pystray.MenuItem(
                "Open Config Folder",
                self._open_config_folder
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Exit",
                self._quit
            )
        )
    
    def run(self):
        self._running = True
        
        self.monitor.start()
        
        self._icon = pystray.Icon(
            "DynamicPowerPlan",
            self._icon_normal,
            "Dynamic Power Plan - Normal",
            menu=self._create_menu()
        )
        
        self._icon.run()
