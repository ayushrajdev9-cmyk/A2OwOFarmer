#!/usr/bin/env python3
"""
A2 OWO FARMER - Unified Launcher
Made by Ayush Rajdev & Anzar Iqbal
"""

import os
import sys
import subprocess
from importlib.metadata import version, PackageNotFoundError

def ensure_dependencies():
    target_hash = "20ae80b"
    try:
        if target_hash in version("discord.py-self"):
            return
    except:
        pass
    is_mobile = os.path.exists("/data/data/com.termux")
    print(f"\n[!] Missing or wrong library. Repairing (20ae80b)...")
    try:
        if is_mobile:
            subprocess.run(["pkg", "install", "git", "-y"], capture_output=True)
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "discord.py", "discord.py-self"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "git+https://github.com/dolfies/discord.py-self@20ae80b398ec83fa272f0a96812140e14868c88"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] Fixed. Restarting...\n")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except:
        sys.exit(1)

ensure_dependencies()

import asyncio
import json
import threading
import time
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.align import Align
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

BANNER = """
[bold red]████████   ██████    ██████  [/bold red][bold white] ██████  ██    ██ ██████ [/bold white]
[bold red]   ██     ██  ██   ██  ██ [/bold red][bold white] ██    ██ ██    ██ ██    ██[/bold white]
[bold red]   ██     ██  ██   ██  ██ [/bold red][bold white] ██    ██ ██    ██ ██    ██[/bold white]
[bold red]   ██     ██  ██   ██  ██ [/bold red][bold white] ██    ██ ██    ██ ██    ██[/bold white]
[bold red]   ██     ██████    ██████ [/bold red][bold white]  ██████   ██████  ██████ [/bold white]
[bold red]   ██       ██        ██  [/bold red][bold white]       ██      ██  ██    ██[/bold white]
[bold red]  ████     ████      ████ [/bold red][bold white] ██████      ██   ██   ██ [/bold white]
"""

CREDITS = "[bold cyan]Made by Ayush Rajdev & Anzar Iqbal[/bold cyan]"

def show_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print(Align.center(BANNER))
    console.print(Align.center("─" * 50))
    console.print(Align.center(CREDITS))
    console.print(Align.center("─" * 50))
    console.print()

def run_neuraself():
    from neura import main as neura_main
    asyncio.run(neura_main())

def run_blackjack_farm():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        import cogs.blackjack_farm as bj
        config_file = "config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                cfg = json.load(f)
            token = cfg.get("TOKEN", "")
            if not token or "YOUR_TOKEN_HERE" in token:
                console.print("[bold red]No token configured in config.json[/bold red]")
                console.print("[yellow]Create config.json with: {\"TOKEN\": \"your_token\", \"BET_SEQUENCE\": \"Low\"}[/yellow]")
                input("Press Enter to return...")
                return
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            bj.run_standalone(token)
        else:
            console.print("[bold red]config.json not found![/bold red]")
            input("Press Enter to return...")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        input("Press Enter to return...")

def run_auto_farm():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    console.print("[bold yellow]Auto Farm requires a standalone token.[/bold yellow]")
    token = Prompt.ask("Enter your Discord token", default="")
    if not token:
        return
    try:
        import cogs.auto_farm as af
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        af.run_standalone(token)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        input("Press Enter to return...")

def run_dashboard():
    from dashboard.app import app as flask_app
    console.print("[bold green]Starting Dashboard on http://0.0.0.0:8000[/bold green]")
    flask_app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)

def main():
    while True:
        show_banner()
        console.print(Panel.fit(
            "[bold cyan][1][/bold cyan] Start NeuraSelf (Advanced Farming)\n"
            "[bold cyan][2][/bold cyan] Start Blackjack Farm\n"
            "[bold cyan][3][/bold cyan] Start Auto Farm\n"
            "[bold cyan][4][/bold cyan] Dashboard\n"
            "[bold cyan][5][/bold cyan] Exit",
            title="[bold yellow]MENU[/bold yellow]",
            border_style="red"
        ))
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="1")
        if choice == "1":
            run_neuraself()
        elif choice == "2":
            run_blackjack_farm()
        elif choice == "3":
            run_auto_farm()
        elif choice == "4":
            run_dashboard()
        else:
            console.print("[yellow]Goodbye![/yellow]")
            sys.exit(0)

if __name__ == "__main__":
    main()
