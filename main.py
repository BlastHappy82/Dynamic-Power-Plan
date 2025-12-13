#!/usr/bin/env python3
"""
Dynamic Power Plan Tray Application

A system tray application that automatically switches Windows power plans
and Lian Li fan configurations based on CPU/GPU usage or running applications.

Usage:
    python main.py [--config PATH]
    
Arguments:
    --config PATH   Path to custom config file (optional)
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.tray_app import TrayApp


def main():
    parser = argparse.ArgumentParser(
        description='Dynamic Power Plan Tray Application'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        default=None,
        help='Path to custom config file'
    )
    
    args = parser.parse_args()
    
    config = Config(args.config)
    
    print(f"Config file: {config.config_path}")
    print(f"Normal plan: {config.normal_plan}")
    print(f"Boost plan: {config.boost_plan}")
    print(f"CPU threshold: {config.cpu_threshold}%")
    print(f"GPU threshold: {config.gpu_threshold}%")
    print(f"Watched games: {config.watched_games}")
    print()
    print("Starting tray application...")
    
    app = TrayApp(config)
    app.run()


if __name__ == '__main__':
    main()
