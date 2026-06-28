"""
A2 OWO FARMER
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

# ─── Auto Farm State ───
auto_farm_active = False

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

BJ_SEQ = {"Low": [488, 976, 1952, 3904, 7808, 15616, 31232, 62464, 124928, 249856], "High": [10000, 25000, 50000, 100000, 180000, 240000]}

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

# ═══════════════════════════════════════
#  AUTO FARM COMMANDS
# ═══════════════════════════════════════

@bot.command()
async def help(ctx):
    await ctx.reply(
        "**A2 OWO FARMER**\n"
        f"Prefix: `{PREFIX}`\n\n"
        "**Auto Farm:**\n"
        f"`{PREFIX}autofarm` - Start auto hunt/sell/flip/cash loop\n"
        f"`{PREFIX}stopfarm` - Stop the loop\n\n"
        "**Blackjack Farm:**\n"
        f"`{PREFIX}bj` - Start blackjack farming\n"
        f"`{PREFIX}bjstop` - Stop blackjack\n"
        f"`{PREFIX}bjtimer 30m` - Set auto-stop timer\n"
        f"`{PREFIX}bjstoponloss 500k` - Stop at loss limit\n"
        f"`{PREFIX}bjbets Low/High` - Change bet sequence\n"
        f"`{PREFIX}bjstatus` - Show stats\n\n"
        "**Made by Ayush Rajdev & Anzar Iqbal**"
    )

@bot.command()
async def autofarm(ctx):
    global auto_farm_active
    if auto_farm_active:
        return await ctx.reply("Auto farm already running! Use `.stopfarm` to stop.")
    await ctx.message.delete()
    await ctx.send("**A2 OWO FARMER - Auto Farm Enabled**\n**Made by Ayush Rajdev & Anzar Iqbal**")
    auto_farm_active = True
    while auto_farm_active:
        await ctx.send("owoh")
        print(f"{Fore.GREEN}owoh{Style.RESET_ALL}")
        await asyncio.sleep(15)
        if not auto_farm_active: break
        await ctx.send("owo sell all")
        print(f"{Fore.GREEN}sell all{Style.RESET_ALL}")
        await asyncio.sleep(2)
        if not auto_farm_active: break
        await ctx.send("owo flip 100")
        print(f"{Fore.GREEN}flip 100{Style.RESET_ALL}")
        await asyncio.sleep(8)
        if not auto_farm_active: break
        await ctx.send("owo cash")
        print(f"{Fore.GREEN}cash{Style.RESET_ALL}")
        await asyncio.sleep(13)
        if not auto_farm_active: break
        await asyncio.sleep(300)

@bot.command()
async def stopfarm(ctx):
    global auto_farm_active
    auto_farm_active = False
    await ctx.reply("Auto farm stopped.")

# ═══════════════════════════════════════
#  BLACKJACK COMMANDS
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
    await ctx.send(f"A2 Blackjack Farm started. Balance: __{bal:,}__ cowoncy.")
    asyncio.create_task(_bj_loop(ctx))

async def _bj_loop(ctx):
    global bj_active
    d = bj_load_data()
    seq_name = "Low"
    while bj_active:
        try:
            if d.get("timer_end") and time.time() >= d["timer_end"]:
                if d["seq_idx"] == 0:
                    bj_active = False; d["timer_end"] = None; bj_save_data(d)
                    await ctx.send("Timer ended. Farm stopped after a win."); return
            sol = d.get("sol_limit", 499224)
            if d.get("profit", 0) < 0 and abs(d["profit"]) >= sol:
                bj_active = False; await ctx.send(f"Stop-on-Loss: __{abs(d['profit']):,}__ loss."); return
            seq = BJ_SEQ.get(seq_name, BJ_SEQ["Low"])
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
            last_react = None
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
async def bjstoponloss(ctx, *, amt=None):
    if not amt: return await ctx.send("Usage: `.bjstoponloss 500k`")
    try:
        lim = parse_amt(amt)
        if lim < 100000: return await ctx.send("Min 100k.")
        d = bj_load_data(); d["sol_limit"] = lim; bj_save_data(d)
        await ctx.send(f"Stop on loss: __{lim:,}__.")
    except: await ctx.send("Invalid format.")

@bot.command()
async def bjbets(ctx, name=None):
    if not name: return await ctx.send("Usage: `.bjbets Low` or `.bjbets High`")
    n = name.capitalize()
    if n not in BJ_SEQ: return await ctx.send("Use `Low` or `High`.")
    open(os.path.join(BOT_DIR, "bj_config.json"),"w").write(json.dumps({"seq":n}))
    await ctx.send(f"Sequence: {n}.")

@bot.command()
async def bjstatus(ctx):
    d = bj_load_data()
    bal = await fetch_balance(ctx)
    if bal: d["curr_balance"] = bal; bj_save_data(d)
    p = d["curr_balance"]-d["start_balance"]
    ps = f"+{p:,}" if p >= 0 else f"{p:,}"
    total = d["wins"]+d["losses"]+d["ties"]
    wp = (d["wins"]/total*100) if total else 0
    await ctx.send(
        f"**A2 BLACKJACK STATUS**\n"
        f"Balance: __{d['start_balance']:,}__ -> __{d['curr_balance']:,}__ ({ps})\n"
        f"Wins: {d['wins']} ({wp:.1f}%) | Losses: {d['losses']} | Ties: {d['ties']}\n"
        f"Commands: {d['cmds']}"
    )

# ═══════════════════════════════════════

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
    print(f"{Fore.YELLOW}Commands: {PREFIX}autofarm, {PREFIX}stopfarm, {PREFIX}bj, {PREFIX}bjstop, {PREFIX}help{Style.RESET_ALL}\n")

    dash_script = os.path.join(BOT_DIR, "web.py")
    if os.path.exists(dash_script):
        subprocess.Popen([sys.executable, dash_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{Fore.GREEN}Dashboard: http://100.75.203.74:6909{Style.RESET_ALL}")

    @bot.event
    async def on_ready():
        act = discord.Activity(type=discord.ActivityType.playing, name="A2 OWO FARMER")
        await bot.change_presence(status=discord.Status.idle, activity=act)
        print(f"{Fore.GREEN}Connected as: {bot.user}{Style.RESET_ALL}")

    bot.run(TOKEN)
