"""
A2 OWO FARMER - Ultimate OwO Bot
Made by Ayush Rajdev & Anzar Iqbal
"""

import discord
from discord.ext import commands
from colorama import Fore, Style, init as colorama_init
import asyncio, json, re, os, time, unicodedata, sys, random
from datetime import datetime
import subprocess

colorama_init()

TOKEN = ""
PREFIX = "."
BOT_DIR = os.path.dirname(os.path.abspath(__file__))

bot = commands.Bot(command_prefix=PREFIX, help_command=None, case_insensitive=True, self_bot=True)

OWO_BOT_ID = 408785106942164992
SETTINGS_FILE = os.path.join(BOT_DIR, "config", "settings.json")
DASHBOARD_FILE = os.path.join(BOT_DIR, "data", "dashboard_stats.json")

def load_settings():
    default = {
        "farming": {
            "autofarm": {"enabled": True, "cycle": ["owoh","owo sell all","owo flip 100","owo cash"], "delays": [15,2,8,13], "rest_interval": 300, "flip_amount": 100},
            "hunt": {"enabled": True, "interval": 18},
            "battle": {"enabled": True, "interval": 20},
            "daily": {"enabled": True},
            "cookie": {"enabled": False, "target_id": ""}
        },
        "blackjack": {
            "bet_sequence": "Low", "stop_on_loss": 500000, "timer_minutes": 0,
            "Low": [488, 976, 1952, 3904, 7808, 15616, 31232, 62464, 124928, 249856],
            "High": [10000, 25000, 50000, 100000, 180000, 240000],
            "Extreme": [50000, 100000, 200000, 400000, 800000, 1600000]
        }
    }
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE) as f:
                return json.load(f)
    except: pass
    return default

def save_settings(s):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=4)

cfg = load_settings()

# ─── Auto Farm State ───
auto_farm_active = False
hunt_task = None
battle_task = None
daily_task = None

# ─── Stats ───
stats = {
    "start_time": time.time(),
    "current_cash": 0,
    "hunt_count": 0, "session_hunt_count": 0,
    "battle_count": 0, "session_battle_count": 0,
    "owo_count": 0, "session_owo_count": 0,
    "other_count": 0, "session_other_count": 0,
    "total_cmd_count": 0,
    "cowoncy_history": [],
    "last_cash_update": 0,
    "username": "A2 Bot",
    "user_id": "local"
}

def format_seconds(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"

def write_dashboard_stats():
    elapsed = time.time() - stats["start_time"]
    mins = elapsed / 60
    session_cmds = stats["session_hunt_count"] + stats["session_battle_count"] + stats["session_owo_count"] + stats["session_other_count"]
    cpm = round(session_cmds / mins, 1) if mins > 0.1 else 0

    cph = 0
    hist = stats["cowoncy_history"]
    if len(hist) > 1:
        first = hist[0]; last = hist[-1]
        time_diff = (last[0] - first[0]) / 3600
        cash_diff = last[1] - first[1]
        if time_diff > 0.01:
            cph = round(cash_diff / time_diff)

    data = {
        "uptime": format_seconds(elapsed),
        "cash": stats["current_cash"],
        "logs": [],
        "status": "ONLINE",
        "security": {"captchas": 0, "bans": 0, "warnings": 0, "last_message": ""},
        "analytics": {"cph": cph, "gems_used": 0},
        "bot": {
            "user_id": stats["user_id"],
            "username": stats["username"],
            "channel_id": None, "paused": False,
            "throttled": False, "cooldown_remaining": 0, "cooldown_command": None
        },
        "chart_data": {
            "hunt": stats["hunt_count"], "battle": stats["battle_count"],
            "session_hunt": stats["session_hunt_count"], "session_battle": stats["session_battle_count"],
            "session_owo": stats["session_owo_count"], "other": stats["other_count"],
            "owo": stats["owo_count"], "total": stats["total_cmd_count"],
            "perf_bpm": cpm
        },
        "system": {"last_cash_update": stats["last_cash_update"], "pending_commands": []},
        "quest_data": [],
        "next_quest_timer": None,
        "cmd_states": {}
    }
    os.makedirs(os.path.dirname(DASHBOARD_FILE), exist_ok=True)
    try:
        with open(DASHBOARD_FILE, "w") as f:
            json.dump(data, f)
    except: pass

async def stats_writer():
    await bot.wait_until_ready()
    while True:
        try:
            write_dashboard_stats()
            await asyncio.sleep(10)
        except: await asyncio.sleep(10)

def track_command(cmd_type):
    stats["total_cmd_count"] += 1
    if cmd_type == "hunt":
        stats["hunt_count"] += 1
        stats["session_hunt_count"] += 1
    elif cmd_type == "battle":
        stats["battle_count"] += 1
        stats["session_battle_count"] += 1
    elif cmd_type == "owo":
        stats["owo_count"] += 1
        stats["session_owo_count"] += 1
    else:
        stats["other_count"] += 1
        stats["session_other_count"] += 1

def parse_cmd_type(text):
    t = text.lower().strip()
    if t.startswith("owo "):
        p = t[4:].split()[0] if t[4:].split() else "owo"
        if p in ("hunt","h"): return "hunt"
        if p in ("battle","b"): return "battle"
        if p == "owo": return "owo"
    return "other"

# ─── Blackjack State ───
bj_active = False
bj_data_file = os.path.join(BOT_DIR, "bj_data.json")

def bj_load_data():
    if os.path.exists(bj_data_file):
        with open(bj_data_file) as f:
            return json.load(f)
    return {"start_balance": 0, "curr_balance": 0, "wins": 0, "losses": 0, "ties": 0, "cmds": 0, "seq_idx": 0, "timer_end": None, "sol_limit": None, "profit": 0}

def bj_save_data(d):
    with open(bj_data_file, "w") as f:
        json.dump(d, f, indent=2)

def parse_time(s):
    t = 0
    s = s.lower()
    h = re.search(r'(\d+)h', s); m = re.search(r'(\d+)m', s); sc = re.search(r'(\d+)s', s)
    if h: t += int(h.group(1))*3600
    if m: t += int(m.group(1))*60
    if sc: t += int(sc.group(1))
    return t

def parse_amt(s):
    s = s.lower().replace(",","")
    if s.endswith('k'): return int(float(s[:-1])*1000)
    if s.endswith('m'): return int(float(s[:-1])*1000000)
    return int(s)

def parse_balance(text):
    m = re.search(r'__([\d,]+)__\s*cowoncy', text, re.I)
    if m: return int(m.group(1).replace(",",""))
    m = re.search(r'([\d,]+)\s*cowoncy', text, re.I)
    if m: return int(m.group(1).replace(",",""))
    return None

def extract_rank(c):
    r = re.match(r"(\d+|a|j|q|k)", c, re.I)
    if not r: return None
    v = r.group(1).lower()
    if v == 'a': return 'A'
    if v in ['j','q','k']: return 10
    return int(v)

def hand_val(cards):
    vals = []; aces = 0
    for c in cards:
        if c == 'A': aces += 1; vals.append(11)
        else: vals.append(c)
    t = sum(vals)
    while t > 21 and aces > 0: t -= 10; aces -= 1
    return t, aces > 0 and t <= 21

def basic_strategy(pt, du, soft):
    dv = du if isinstance(du, int) else (11 if du == 'A' else 10)
    if soft:
        if pt >= 19: return 'stand'
        if pt == 18: return 'stand' if dv <= 8 else 'hit'
        return 'hit'
    if pt >= 17: return 'stand'
    if pt >= 13: return 'stand' if dv <= 6 else 'hit'
    if pt == 12: return 'stand' if dv in [4,5,6] else 'hit'
    return 'hit'

def parse_game(text):
    card_pat = r":([^:]+):"
    dm = re.search(r"Dealer \[([^+?]+)\+?\?\]", text)
    if not dm: raise ValueError("No dealer")
    du = extract_rank(dm.group(1).strip())
    lines = text.splitlines(); pcs = []
    for i, ln in enumerate(lines):
        if re.search(r"\[\d+\*?\]", ln) and "dealer" not in ln.lower():
            for j in range(i+1, min(i+3, len(lines))):
                for c in re.findall(card_pat, lines[j]): pcs.append(c)
            break
    if not pcs:
        pcs = [c for c in re.findall(card_pat, text) if c not in ["cardback", dm.group(1).strip()] and "?" not in c]
    vals = []
    for c in pcs:
        try: vals.append(extract_rank(c))
        except: pass
    t, s = hand_val(vals)
    return du, vals, s

def get_owo_text(msg):
    parts = [msg.content or ""]
    if msg.embeds:
        e = msg.embeds[0]
        if e.author and e.author.name: parts.append(e.author.name)
        if e.description: parts.append(e.description)
        for f in e.fields:
            if f.name: parts.append(f.name)
            if f.value: parts.append(f.value)
        if e.footer and e.footer.text: parts.append(e.footer.text)
    return "\n".join(parts)

async def fetch_balance(ctx):
    last_id = None
    try:
        for m in await ctx.channel.history(limit=10).flatten():
            if m.author.id == OWO_BOT_ID: last_id = m.id; break
    except: pass
    await ctx.send("owo cash")
    for _ in range(10):
        await asyncio.sleep(1.5)
        try:
            for m in await ctx.channel.history(limit=10).flatten():
                if m.author.id != OWO_BOT_ID: continue
                if last_id and m.id <= last_id: continue
                t = get_owo_text(m)
                if "cowoncy" in t.lower():
                    b = parse_balance(t)
                    if b: return b
        except: pass
    return None

async def safe_send(channel, text):
    try:
        await channel.send(text)
        print(f"{Fore.GREEN}[SEND] {text}{Style.RESET_ALL}")
        cmd_type = parse_cmd_type(text)
        track_command(cmd_type)
        if "cash" in text.lower().split():
            await asyncio.sleep(3)
            try:
                for m in await channel.history(limit=5).flatten():
                    if m.author.id == OWO_BOT_ID:
                        t = get_owo_text(m)
                        b = parse_balance(t)
                        if b:
                            stats["current_cash"] = b
                            stats["last_cash_update"] = time.time()
                            stats["cowoncy_history"].append((time.time(), b))
                            if len(stats["cowoncy_history"]) > 100:
                                stats["cowoncy_history"].pop(0)
                        break
            except: pass
        return True
    except Exception as e:
        print(f"{Fore.RED}[SEND ERROR] {e}{Style.RESET_ALL}")
        return False

# ═══════════════════════════════════════
#  AUTO FARM SCHEDULER
# ═══════════════════════════════════════

async def auto_hunt_loop(ctx):
    global hunt_task
    await bot.wait_until_ready()
    while True:
        try:
            fc = cfg.get("farming", {})
            if fc.get("hunt", {}).get("enabled", True):
                await safe_send(ctx.channel, "owo hunt")
            await asyncio.sleep(fc.get("hunt", {}).get("interval", 18))
        except asyncio.CancelledError: break
        except: await asyncio.sleep(10)

async def auto_battle_loop(ctx):
    global battle_task
    await bot.wait_until_ready()
    while True:
        try:
            fc = cfg.get("farming", {})
            if fc.get("battle", {}).get("enabled", True):
                await safe_send(ctx.channel, "owo battle")
            await asyncio.sleep(fc.get("battle", {}).get("interval", 20))
        except asyncio.CancelledError: break
        except: await asyncio.sleep(10)

async def auto_daily_loop(ctx):
    await bot.wait_until_ready()
    while True:
        try:
            fc = cfg.get("farming", {})
            if fc.get("daily", {}).get("enabled", True):
                await safe_send(ctx.channel, "owo daily")
            await asyncio.sleep(86400)
        except asyncio.CancelledError: break
        except: await asyncio.sleep(60)

# ═══════════════════════════════════════
#  COMMANDS
# ═══════════════════════════════════════

@bot.command()
async def help(ctx):
    c = cfg.get("farming", {}).get("autofarm", {})
    flip = c.get("flip_amount", 100)
    seq = cfg.get("blackjack", {}).get("bet_sequence", "Low")
    await ctx.reply(
        "**A2 OWO FARMER**\n"
        f"Prefix: `{PREFIX}`\n\n"
        "**💰 Auto Farm:**\n"
        f"`{PREFIX}af` - Start auto farm loop (flip {flip})\n"
        f"`{PREFIX}sf` - Stop auto farm\n"
        f"`{PREFIX}hunt` - Start auto hunt every 18s\n"
        f"`{PREFIX}battle` - Start auto battle every 20s\n"
        f"`{PREFIX}stophunt` - Stop hunt loop\n"
        f"`{PREFIX}stopbattle` - Stop battle loop\n\n"
        "**♠️ Blackjack:**\n"
        f"`{PREFIX}bj` - Start blackjack (seq: {seq})\n"
        f"`{PREFIX}bjstop` - Stop blackjack\n"
        f"`{PREFIX}bjtimer 30m` - Auto-stop timer\n"
        f"`{PREFIX}bjloss 500k` - Stop on loss limit\n"
        f"`{PREFIX}bjseq Low/High/Extreme` - Bet sequence\n"
        f"`{PREFIX}bjst` - Blackjack stats\n\n"
        "**⚙️ Config:**\n"
        f"`{PREFIX}flip <amount>` - Set flip amount\n"
        f"`{PREFIX}reload` - Reload settings\n"
        f"`{PREFIX}bal` - Check balance\n\n"
        "**Made by Ayush Rajdev & Anzar Iqbal**"
    )

@bot.command(aliases=["af"])
async def autofarm(ctx):
    global auto_farm_active
    if auto_farm_active:
        return await ctx.reply("Auto farm already running! Use `.sf` to stop.")
    await ctx.message.delete()
    fc = cfg.get("farming", {}).get("autofarm", {})
    flip = fc.get("flip_amount", 100)
    rest = fc.get("rest_interval", 300)
    await ctx.send(f"**A2 FARM STARTED** (flip {flip})")
    auto_farm_active = True
    while auto_farm_active:
        await safe_send(ctx.channel, "owoh")
        await asyncio.sleep(15)
        if not auto_farm_active: break
        await safe_send(ctx.channel, "owo sell all")
        await asyncio.sleep(2)
        if not auto_farm_active: break
        await safe_send(ctx.channel, f"owo flip {flip}")
        await asyncio.sleep(8)
        if not auto_farm_active: break
        await safe_send(ctx.channel, "owo cash")
        await asyncio.sleep(13)
        if not auto_farm_active: break
        await asyncio.sleep(rest)

@bot.command(aliases=["sf"])
async def stopfarm(ctx):
    global auto_farm_active
    auto_farm_active = False
    await ctx.reply("Auto farm stopped.")

@bot.command()
async def hunt(ctx):
    global hunt_task
    if hunt_task and not hunt_task.done():
        return await ctx.reply("Hunt loop already running! Use `.stophunt` first.")
    await ctx.send("**Auto hunt started** (every 18s)")
    hunt_task = asyncio.create_task(auto_hunt_loop(ctx))

@bot.command()
async def stophunt(ctx):
    global hunt_task
    if hunt_task:
        hunt_task.cancel(); hunt_task = None
    await ctx.reply("Hunt stopped.")

@bot.command()
async def battle(ctx):
    global battle_task
    if battle_task and not battle_task.done():
        return await ctx.reply("Battle loop already running!")
    await ctx.send("**Auto battle started** (every 20s)")
    battle_task = asyncio.create_task(auto_battle_loop(ctx))

@bot.command()
async def stopbattle(ctx):
    global battle_task
    if battle_task:
        battle_task.cancel(); battle_task = None
    await ctx.reply("Battle stopped.")

@bot.command(aliases=["bal"])
async def balance(ctx):
    bal = await fetch_balance(ctx)
    if bal:
        stats["current_cash"] = bal
        stats["last_cash_update"] = time.time()
        await ctx.reply(f"Balance: **__{bal:,}__** cowoncy")
    else: await ctx.reply("Couldn't fetch balance.")

@bot.command()
async def flip(ctx, amount=None):
    global cfg
    if not amount: return await ctx.reply("Usage: `.flip 500`")
    try:
        amt = int(amount)
        cfg.setdefault("farming", {}).setdefault("autofarm", {})["flip_amount"] = amt
        save_settings(cfg)
        await ctx.reply(f"Flip amount set to **{amt}**")
    except: await ctx.reply("Invalid amount.")

@bot.command()
async def reload(ctx):
    global cfg
    cfg = load_settings()
    await ctx.reply("Settings reloaded from config/settings.json")

# ═══════════════════════════════════════
#  BLACKJACK
# ═══════════════════════════════════════

@bot.command()
async def bj(ctx):
    global bj_active
    if bj_active:
        return await ctx.send("Blackjack already running! Use `.bjstop` first.")
    bal = await fetch_balance(ctx)
    if not bal: return await ctx.send("Can't fetch balance.")
    d = bj_load_data()
    d.update({"start_balance": bal, "curr_balance": bal, "wins": 0, "losses": 0, "ties": 0, "cmds": 0, "seq_idx": 0, "profit": 0})
    bj_save_data(d)
    bj_active = True
    seq = cfg.get("blackjack", {}).get("bet_sequence", "Low")
    await ctx.send(f"A2 Blackjack started. Balance: __{bal:,}__ | Seq: {seq}")
    asyncio.create_task(_bj_loop(ctx))

async def _bj_loop(ctx):
    global bj_active
    d = bj_load_data()
    while bj_active:
        try:
            bc = cfg.get("blackjack", {})
            seq_name = bc.get("bet_sequence", "Low")
            sol_limit = bc.get("stop_on_loss", 500000)

            if d.get("timer_end") and time.time() >= d["timer_end"]:
                if d["seq_idx"] == 0:
                    bj_active = False; d["timer_end"] = None; bj_save_data(d)
                    await ctx.send("Timer ended. Farm stopped after a win."); return

            sol = d.get("sol_limit", sol_limit)
            if d.get("profit", 0) < 0 and abs(d["profit"]) >= sol:
                bj_active = False; await ctx.send(f"Stop-on-Loss: __{abs(d['profit']):,}__"); return

            seq = bc.get(seq_name, bc.get("Low", [488, 976, 1952, 3904, 7808, 15616, 31232, 62464, 124928, 249856]))
            if d["seq_idx"] >= len(seq): d["seq_idx"] = 0
            bet = seq[d["seq_idx"]]
            d["cmds"] += 1; bj_save_data(d)
            await asyncio.sleep(random.uniform(4, 17))
            last_id = None
            try:
                for m in await ctx.channel.history(limit=10).flatten():
                    if m.author.id == OWO_BOT_ID: last_id = m.id; break
            except: pass
            await ctx.send(f"owo bj {bet}")
            msg = None
            for _ in range(10):
                await asyncio.sleep(1.5)
                try:
                    for m in await ctx.channel.history(limit=10).flatten():
                        if m.author.id != OWO_BOT_ID or (last_id and m.id <= last_id) or not m.embeds: continue
                        msg = m; break
                    if msg: break
                except: pass
            if not msg: continue
            while bj_active:
                try:
                    await asyncio.sleep(2)
                    for m in await ctx.channel.history(limit=10).flatten():
                        if m.id == msg.id: msg = m; break
                except: pass
                ft = get_owo_text(msg)
                footer = (msg.embeds[0].footer.text or "").lower().strip() if msg.embeds and msg.embeds[0].footer else ""
                if "game in progress" not in footer:
                    if "won" in footer and "lost" not in footer:
                        d["wins"] += 1; d["profit"] += bet; d["seq_idx"] = 0
                        print(f"{Fore.GREEN}[BJ WIN] +{bet:,}{Style.RESET_ALL}")
                        bj_save_data(d); break
                    elif "tied" in footer or "both bust" in footer:
                        d["ties"] += 1; bj_save_data(d); break
                    elif "lost" in footer or ("bust" in footer and "both" not in footer):
                        d["losses"] += 1; d["profit"] -= bet; d["seq_idx"] += 1
                        print(f"{Fore.RED}[BJ LOSS] -{bet:,}{Style.RESET_ALL}")
                        bj_save_data(d); break
                    else: await asyncio.sleep(2); continue
                try:
                    du, pv, sft = parse_game(ft)
                    pt, _ = hand_val(pv)
                    act = basic_strategy(pt, du, sft)
                    emoji = "👊" if act == "hit" else "🛑"
                    await msg.add_reaction(emoji)
                    print(f"{Fore.YELLOW}[BJ] {pv} total={pt} -> {act}{Style.RESET_ALL}")
                except: pass
                await asyncio.sleep(3)
            await asyncio.sleep(4)
        except Exception as e:
            print(f"{Fore.RED}[BJ ERROR] {e}{Style.RESET_ALL}")
            await asyncio.sleep(5)
    print(f"{Fore.YELLOW}[BJ] Stopped.{Style.RESET_ALL}")

@bot.command()
async def bjstop(ctx):
    global bj_active
    bj_active = False
    d = bj_load_data(); d["timer_end"] = None; bj_save_data(d)
    await ctx.send("Blackjack stopped.")

@bot.command()
async def bjtimer(ctx, *, t=None):
    if not t: return await ctx.send("Usage: `.bjtimer 30m`")
    s = parse_time(t)
    if s < 300: return await ctx.send("Min 5 minutes.")
    d = bj_load_data(); d["timer_end"] = time.time()+s; bj_save_data(d)
    await ctx.send(f"Timer set for {t}.")

@bot.command()
async def bjloss(ctx, *, amt=None):
    if not amt: return await ctx.send("Usage: `.bjloss 500k`")
    try:
        lim = parse_amt(amt)
        if lim < 100000: return await ctx.send("Min 100k.")
        d = bj_load_data(); d["sol_limit"] = lim; bj_save_data(d)
        await ctx.send(f"Stop on loss: __{lim:,}__.")
    except: await ctx.send("Invalid format.")

@bot.command()
async def bjseq(ctx, name=None):
    global cfg
    if not name: return await ctx.send("Usage: `.bjseq Low/High/Extreme`")
    n = name.capitalize()
    valid = cfg.get("blackjack", {})
    if n not in ["Low","High","Extreme"]: return await ctx.send("Use `Low`, `High`, or `Extreme`.")
    cfg["blackjack"]["bet_sequence"] = n
    save_settings(cfg)
    await ctx.send(f"Bet sequence: **{n}**.")

@bot.command(aliases=["bjst"])
async def bjstatus(ctx):
    d = bj_load_data()
    bal = await fetch_balance(ctx)
    if bal: d["curr_balance"] = bal; bj_save_data(d)
    p = d["curr_balance"]-d["start_balance"]
    ps = f"+{p:,}" if p >= 0 else f"{p:,}"
    total = d["wins"]+d["losses"]+d["ties"]
    wp = (d["wins"]/total*100) if total else 0
    await ctx.send(
        f"**A2 BLACKJACK**\n"
        f"Balance: __{d['start_balance']:,}__ -> __{d['curr_balance']:,}__ ({ps})\n"
        f"Wins: {d['wins']} ({wp:.1f}%) | Losses: {d['losses']} | Ties: {d['ties']}\n"
        f"Commands: {d['cmds']}"
    )

# ═══════════════════════════════════════

@bot.event
async def on_ready():
    act = discord.Activity(type=discord.ActivityType.playing, name="A2 OWO FARMER")
    await bot.change_presence(status=discord.Status.idle, activity=act)
    stats["username"] = str(bot.user)
    stats["user_id"] = str(bot.user.id)
    print(f"{Fore.GREEN}Connected as: {bot.user}{Style.RESET_ALL}")
    asyncio.create_task(stats_writer())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        TOKEN = sys.argv[1]
    else:
        TOKEN = input("Enter Discord token: ").strip()

    print(f"""{Fore.CYAN}
    ██████   ██████       ██████  ██    ██ ██████ 
   ██  ██   ██  ██      ██    ██ ██    ██ ██    ██
   ██  ██   ██  ██      ██    ██ ██    ██ ██    ██
   ██  ██   ██  ██      ██    ██ ██    ██ ██    ██
   ██████    ██████      ██████   ██████  ██████ 
     ██        ██              ██      ██  ██    ██
    ████      ████       ██████      ██   ██   ██ 
{Style.RESET_ALL}""")
    print(f"{Fore.GREEN}A2 OWO FARMER - Made by Ayush Rajdev & Anzar Iqbal{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Commands: {PREFIX}af, {PREFIX}hunt, {PREFIX}battle, {PREFIX}bj, {PREFIX}help{Style.RESET_ALL}\n")

    dash_script = os.path.join(BOT_DIR, "web.py")
    if os.path.exists(dash_script):
        subprocess.Popen([sys.executable, dash_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    flask_script = os.path.join(BOT_DIR, "run_flask.sh")
    if os.path.exists(flask_script):
        subprocess.Popen(["bash", flask_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"{Fore.GREEN}Dashboard: http://100.75.203.74:6909{Style.RESET_ALL}")

    bot.run(TOKEN)
