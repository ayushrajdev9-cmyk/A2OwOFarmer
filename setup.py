#!/usr/bin/env python3
"""
A2 OWO FARMER - Setup Script
Made by Ayush Rajdev & Anzar Iqbal
Installs dependencies and prepares the environment.
"""

import os
import sys
import subprocess
import json
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")

def install_requirements():
    print("[*] Installing requirements...")
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    if os.path.exists(req_file):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
            print("[+] Requirements installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"[!] pip install failed: {e}")
            sys.exit(1)
    else:
        print("[!] requirements.txt not found!")
        sys.exit(1)

def ensure_config():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        print("[+] Created config directory.")
    
    accounts_file = os.path.join(CONFIG_DIR, "accounts.json")
    if not os.path.exists(accounts_file):
        with open(accounts_file, "w") as f:
            json.dump({"accounts": []}, f, indent=4)
        print("[+] Created accounts.json template.")
    
    settings_file = os.path.join(CONFIG_DIR, "settings.json")
    if not os.path.exists(settings_file):
        default_settings = {
            "core": {"prefix": "owo ", "monitor_bot_id": "408785106942164992"},
            "stealth": {"typing": {"enabled": False}},
            "commands": {
                "hunt": {"enabled": True, "cooldown": [15, 18]},
                "battle": {"enabled": True, "cooldown": [15, 18]},
                "owo": {"enabled": True, "cooldown": [10, 13]}
            }
        }
        with open(settings_file, "w") as f:
            json.dump(default_settings, f, indent=4)
        print("[+] Created settings.json template.")

def main():
    print("=" * 60)
    print("  A2 OWO FARMER - Setup")
    print("  Made by Ayush Rajdev & Anzar Iqbal")
    print("=" * 60)
    print()
    install_requirements()
    ensure_config()
    print()
    print("[+] Setup complete! Run: python run.py")
    print()

if __name__ == "__main__":
    main()
