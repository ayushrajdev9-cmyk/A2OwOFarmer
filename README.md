<div align="center">

# A2 OWO FARMER

**Ultimate OwO Bot Farming Suite**

<img src="https://readme-typing-svg.herokuapp.com/?font=Pacifico&size=40&pause=1000&color=FF0000&center=true&vCenter=true&random=false&width=600&lines=Ultimate+OwO+Bot+Farming+Suite;Made+by+Ayush+Rajdev+%26+Anzar+Iqbal" alt="A2 OWO FARMER">

</div>

---

## Description

**A2 OWO FARMER** is the ultimate combined OwO bot farming suite, bringing together three powerful bots:

1. **NeuraSelf** - Advanced OwO automation with human-like behavior, multi-layer security, and web dashboard
2. **Blackjack Farm** - Automated Blackjack farming with smart betting strategies
3. **Auto Farm** - Simple auto-farming with hunting, battling, and selling

All in one unified launcher with a single `run.py` entry point.

---

## Features

### NeuraSelf (Advanced Farming)
- Auto HuntBot solving with image recognition
- Captcha solving (web + letter image)
- Auto gems (Fabled/Legendary/mixed)
- Multi-account support with independent configs
- Dynamic quest intelligence
- Stealth typing simulation
- Premium web dashboard with live stats
- Security system (auto-pause, captcha detection)

### Blackjack Farm
- Automated blackjack with basic strategy
- Smart bet sequencing (Low/High)
- Win/Loss tracking
- Timer and stop-loss controls
- CAPTCHA warning detection

### Auto Farm
- Continuous auto-hunting
- Auto-selling
- Cowoncy flipping
- Balance tracking

---

## Installation

### Prerequisites
- Python 3.10+
- Git

### Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd A2OwoFarmer
   ```

2. Run the setup script:
   ```bash
   python setup.py
   ```

3. Configure your accounts:
   ```bash
   python run.py
   ```
   Then select option 2 from the NeuraSelf menu to manage accounts.

---

## Usage

Start the unified launcher:

```bash
python run.py
```

You will see a menu with options:
- **[1] Start NeuraSelf** - Advanced farming with all features
- **[2] Start Blackjack Farm** - Automated blackjack farming
- **[3] Start Auto Farm** - Simple auto-farming
- **[4] Dashboard** - Web dashboard (while NeuraSelf runs)
- **[5] Exit**

### Standalone Mode

You can also run each bot independently:

```bash
# NeuraSelf
python neura.py

# Blackjack Farm (requires config.json)
python -c "from cogs.blackjack_farm import run_standalone; run_standalone('YOUR_TOKEN')"

# Auto Farm
python -c "from cogs.auto_farm import run_standalone; run_standalone('YOUR_TOKEN')"
```

---

## Configuration

### NeuraSelf Accounts
Edit `config/accounts.json` to add your Discord tokens and channel IDs.

### Blackjack Farm Config
Create `config.json` in the root directory:
```json
{
    "TOKEN": "YOUR_DISCORD_TOKEN",
    "BET_SEQUENCE": "Low"
}
```

---

## Disclaimer

This tool is for **educational purposes only**. Using self-bots violates Discord's Terms of Service and may result in account termination. Use only in private servers and do not openly share that you are using automation.

---

<div align="center">

**A2 OWO FARMER** • Made by **Ayush Rajdev & Anzar Iqbal** • Made with ❤️

</div>
