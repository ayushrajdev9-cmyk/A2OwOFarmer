# A2 OWO FARMER - Combined OwO Bot Suite
# Made by Ayush Rajdev & Anzar Iqbal

"""
A2OwoFarmer OwO BlackJack Farm Module
"""

import discord
from discord.ext import commands
from colorama import Fore, Style, init as colorama_init
import asyncio, json, re, os, time, unicodedata, sys
from datetime import datetime
import random

colorama_init()

OT = commands.Bot
farming_active = False
farm_task = None
DATA_FILE = "data.json"
OWO_BOT_ID = 408785106942164992

def parse_time_to_seconds(time_str):
    seconds = 0
    time_str = time_str.lower()
    hours = re.search(r'(\d+)h', time_str)
    mins = re.search(r'(\d+)m', time_str)
    secs = re.search(r'(\d+)s', time_str)
    if hours: seconds += int(hours.group(1)) * 3600
    if mins: seconds += int(mins.group(1)) * 60
    if secs: seconds += int(secs.group(1))
    return seconds

def parse_amount(amt_str):
    amt_str = amt_str.lower().replace(",", "")
    if amt_str.endswith('k'):
        return int(float(amt_str[:-1]) * 1000)
    elif amt_str.endswith('m'):
        return int(float(amt_str[:-1]) * 1000000)
    else:
        return int(amt_str)

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {"TOKEN": "", "BET_SEQUENCE": "Low"}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "start_timestamp": None,
        "starting_balance": 0,
        "current_balance": 0,
        "wins": 0,
        "losses": 0,
        "ties": 0,
        "commands_used": 0,
        "seq_index": 0,
        "timer_end": None,
        "stop_on_loss_limit": None,
        "internal_profit": 0
    }

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

data = load_data()
data["timer_end"] = None
save_data(data)
config = load_config()

BET_SEQUENCES = {
    "Low": [488, 976, 1952, 3904, 7808, 15616, 31232, 62464, 124928, 249856],
    "High": [10000, 25000, 50000, 100000, 180000, 240000]
}

def parse_balance(text):
    match = re.search(r'__([\d,]+)__\s*cowoncy', text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    match = re.search(r'([\d,]+)\s*cowoncy', text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    return None

def extract_rank(card_str):
    rank_part = re.match(r"(\d+|a|j|q|k)", card_str, re.I)
    if not rank_part:
        return None
    rank = rank_part.group(1).lower()
    if rank == 'a':
        return 'A'
    elif rank in ['j', 'q', 'k']:
        return 10
    return int(rank)

def hand_value(cards):
    values = []
    aces = 0
    for c in cards:
        if c == 'A':
            aces += 1
            values.append(11)
        else:
            values.append(c)
    total = sum(values)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    soft = (aces > 0 and total <= 21)
    return total, soft

def basic_strategy(player_total, dealer_upcard, soft):
    dealer_val = dealer_upcard if isinstance(dealer_upcard, int) else (11 if dealer_upcard == 'A' else 10)
    if soft:
        if player_total >= 19:
            return 'stand'
        elif player_total == 18:
            return 'stand' if dealer_val <= 8 else 'hit'
        else:
            return 'hit'
    else:
        if player_total >= 17:
            return 'stand'
        elif player_total >= 13:
            return 'stand' if dealer_val <= 6 else 'hit'
        elif player_total == 12:
            return 'stand' if dealer_val in [4, 5, 6] else 'hit'
        else:
            return 'hit'

def decide(text):
    try:
        clean = text.replace("`", "")
        dealer_rank, player_values, soft = parse_game_state(clean)
        total, soft = hand_value(player_values)
        action = basic_strategy(total, dealer_rank, soft)
        print(f"{Fore.YELLOW}[DECIDE] Cards={player_values} total={total} soft={soft} dealer={dealer_rank} -> {action}{Style.RESET_ALL}")
        return action
    except Exception as e:
        print(f"{Fore.RED}[DECIDE ERROR] {e}{Style.RESET_ALL}")
        return 'stand'

def parse_game_state(text):
    card_pattern = r":([^:]+):"
    dealer_match = re.search(r"Dealer \[([^+?]+)\+?\?\]", text)
    if not dealer_match:
        raise ValueError("Could not find dealer upcard")
    dealer_rank_str = dealer_match.group(1).strip()
    dealer_rank = extract_rank(dealer_rank_str)
    lines = text.splitlines()
    player_cards = []
    for i, line in enumerate(lines):
        if re.search(r"\[\d+\*?\]", line) and not re.search(r"[Dd]ealer", line):
            for j in range(i + 1, min(i + 3, len(lines))):
                card_matches = re.findall(card_pattern, lines[j])
                for cm in card_matches:
                    player_cards.append(cm)
            break
    if not player_cards:
        all_cards = re.findall(card_pattern, text)
        player_cards = [c for c in all_cards if c not in ["cardback", dealer_rank_str] and "?" not in c]
    values = []
    for card in player_cards:
        try:
            rank = extract_rank(card)
            values.append(rank)
        except Exception:
            continue
    total, soft = hand_value(values)
    return dealer_rank, values, soft

def get_owo_text(msg):
    parts = []
    if msg.content:
        parts.append(msg.content)
    if msg.embeds:
        embed = msg.embeds[0]
        if embed.author and embed.author.name:
            parts.append(embed.author.name)
        if embed.description:
            parts.append(embed.description)
        for field in embed.fields:
            if field.name:
                parts.append(field.name)
            if field.value:
                parts.append(field.value)
        if embed.footer and embed.footer.text:
            parts.append(embed.footer.text)
    return "\n".join(parts)

async def fetch_owo_balance(ctx):
    last_owo_id = None
    try:
        pre_history = await ctx.channel.history(limit=10).flatten()
        for m in pre_history:
            if m.author.id == OWO_BOT_ID:
                last_owo_id = m.id
                break
    except Exception as e:
        print(f"{Fore.RED}[snapshot error] {e}{Style.RESET_ALL}")
    await ctx.send("owo cash")
    for attempt in range(10):
        await asyncio.sleep(1.5)
        try:
            messages = await ctx.channel.history(limit=10).flatten()
            for msg in messages:
                if msg.author.id != OWO_BOT_ID:
                    continue
                if last_owo_id and msg.id <= last_owo_id:
                    continue
                text = get_owo_text(msg)
                if "cowoncy" in text.lower():
                    balance = parse_balance(text)
                    if balance is not None:
                        print(f"{Fore.GREEN}[BALANCE] Fetched: {balance:,}{Style.RESET_ALL}")
                        return balance
        except Exception as e:
            print(f"{Fore.RED}[fetch error] {e}{Style.RESET_ALL}")
    print(f"{Fore.RED}[BALANCE] No fresh cowoncy response found.{Style.RESET_ALL}")
    return None

async def check_warning(ctx):
    if not farming_active:
        return True
    try:
        messages = await ctx.channel.history(limit=15).flatten()
        for msg in messages:
            if msg.author.id != OWO_BOT_ID:
                continue
            msg_content = str(msg.content)
            if not msg_content:
                continue
            clean = unicodedata.normalize("NFKC", msg_content)
            clean = re.sub(r'[\u200B-\u200D\uFEFF]', '', clean).lower()
            if "captcha" in clean and "verify" in clean:
                match = re.search(r'[\(\[\{]?\s*(\d+)\s*[\/\u2015]\s*5\s*[\)\]\}]?', clean)
                if match:
                    count = int(match.group(1))
                    print(f"{Fore.YELLOW}CAPTCHA WARNING DETECTED: ({count}/5){Style.RESET_ALL}")
                    if count == 1:
                        return True
        return False
    except Exception as e:
        print(f"{Fore.RED}Warning check error: {e}{Style.RESET_ALL}")
        return False

async def run_farm(ctx):
    global farming_active, data
    farming_active = True
    print(f"{Fore.GREEN}[FARM] Started.{Style.RESET_ALL}")
    seq_idx = data.get("seq_index", 0)
    while farming_active:
        try:
            if data.get("timer_end") and time.time() >= data["timer_end"]:
                if seq_idx == 0:
                    farming_active = False
                    data["timer_end"] = None
                    save_data(data)
                    await ctx.send("Timer ended! Farm stopped safely after a win.")
                    print(f"{Fore.YELLOW}[TIMER] Farm stopped naturally.{Style.RESET_ALL}")
                    return
                else:
                    print(f"{Fore.YELLOW}[TIMER] Time is up, but currently in a losing streak. Playing until next win to stop.{Style.RESET_ALL}")
            cfg = load_config()
            seq_name = cfg.get("BET_SEQUENCE", "Low")
            sol_limit = data.get("stop_on_loss_limit")
            if not sol_limit:
                sol_limit = 499224 if seq_name == "Low" else 605000
            if data.get("internal_profit", 0) < 0 and abs(data["internal_profit"]) >= sol_limit:
                farming_active = False
                await ctx.send(f"Stop-on-Loss Triggered! Net loss reached __{abs(data['internal_profit']):,}__. Farm stopped.")
                print(f"{Fore.RED}[STOP ON LOSS] Farm stopped due to max loss limit.{Style.RESET_ALL}")
                return
            if await check_warning(ctx):
                farming_active = False
                print(f"{Fore.RED}[FARM] Stopped: CAPTCHA WARNING.{Style.RESET_ALL}")
                await ctx.send("WARNING DETECTED! Stopping | SOLVE YOUR CAPTCHA FIRST | Start again to restart.")
                return
            sequence = BET_SEQUENCES.get(seq_name, BET_SEQUENCES["Low"])
            if seq_idx >= len(sequence):
                seq_idx = 0
            bet = sequence[seq_idx]
            data["commands_used"] += 1
            save_data(data)
            await asyncio.sleep(random.uniform(4.1, 16.9))
            print(f"{Fore.CYAN}[ROUND] Betting {bet:,} | idx={seq_idx} | seq={seq_name}{Style.RESET_ALL}")
            last_owo_id = None
            try:
                pre_history = await ctx.channel.history(limit=10).flatten()
                for m in pre_history:
                    if m.author.id == OWO_BOT_ID:
                        last_owo_id = m.id
                        break
            except Exception as e:
                print(f"{Fore.RED}[snapshot error] {e}{Style.RESET_ALL}")
            await ctx.send(f"owo bj {bet}")
            msg = None
            deadline = time.time() + 15
            while time.time() < deadline:
                try:
                    history = await ctx.channel.history(limit=10).flatten()
                    for m in history:
                        if m.author.id != OWO_BOT_ID:
                            continue
                        if last_owo_id and m.id <= last_owo_id:
                            continue
                        if not m.embeds:
                            continue
                        msg = m
                        break
                    if msg:
                        break
                except Exception as e:
                    print(f"{Fore.RED}[wait error] {e}{Style.RESET_ALL}")
                await asyncio.sleep(1.5)
            if not msg:
                print(f"{Fore.YELLOW}[FARM] No OwO embed found, retrying round...{Style.RESET_ALL}")
                await asyncio.sleep(5)
                continue
            last_reaction = None
            while farming_active:
                if await check_warning(ctx):
                    farming_active = False
                    await ctx.send("CAPTCHA WARNING! Stopped. Solve & restart.")
                    return
                try:
                    await asyncio.sleep(2)
                    history = await ctx.channel.history(limit=10).flatten()
                    for m in history:
                        if m.id == msg.id:
                            msg = m
                            break
                except Exception as e:
                    print(f"{Fore.RED}[refetch error] {e}{Style.RESET_ALL}")
                full_text = get_owo_text(msg)
                footer = ""
                if msg.embeds and msg.embeds[0].footer:
                    footer = msg.embeds[0].footer.text or ""
                footer_lower = footer.lower().strip()
                if "game in progress" not in footer_lower:
                    if "won" in footer_lower and "lost" not in footer_lower:
                        data["wins"] += 1
                        data["internal_profit"] = data.get("internal_profit", 0) + bet
                        seq_idx = 0
                        print(f"{Fore.GREEN}[WIN] +{bet:,} -> reset to idx 0{Style.RESET_ALL}")
                        data["seq_index"] = seq_idx
                        save_data(data)
                        break
                    elif "tied" in footer_lower or "both bust" in footer_lower:
                        data["ties"] += 1
                        print(f"{Fore.YELLOW}[TIE] {bet:,} -> same idx {seq_idx}{Style.RESET_ALL}")
                        data["seq_index"] = seq_idx
                        save_data(data)
                        break
                    elif "lost" in footer_lower or ("bust" in footer_lower and "both" not in footer_lower):
                        data["losses"] += 1
                        data["internal_profit"] = data.get("internal_profit", 0) - bet
                        seq_idx += 1
                        print(f"{Fore.RED}[LOSS] -{bet:,} -> next idx {seq_idx}{Style.RESET_ALL}")
                        data["seq_index"] = seq_idx
                        save_data(data)
                        break
                    else:
                        await asyncio.sleep(2)
                        continue
                action = decide(full_text)
                emoji = "\U0001f44a" if action == "hit" else "\U0001f6d1"
                if last_reaction and last_reaction == emoji:
                    try:
                        await msg.remove_reaction(emoji, ctx.bot.user)
                        last_reaction = None
                    except Exception:
                        pass
                elif last_reaction and last_reaction != emoji:
                    try:
                        await msg.add_reaction(emoji)
                        last_reaction = emoji
                    except Exception:
                        pass
                else:
                    try:
                        await msg.add_reaction(emoji)
                        last_reaction = emoji
                    except Exception:
                        pass
                data["commands_used"] += 1
                save_data(data)
                await asyncio.sleep(3)
            await asyncio.sleep(4)
        except Exception as e:
            print(f"{Fore.RED}[FARM ERROR] {e}{Style.RESET_ALL}")
            await asyncio.sleep(5)
    print(f"{Fore.YELLOW}[FARM] Stopped.{Style.RESET_ALL}")


class BlackjackFarm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.log("SYS", "BlackjackFarm cog loaded")

    @commands.command()
    async def bjstart(self, ctx):
        global farming_active, farm_task, data
        if farming_active:
            return await ctx.send("A2OwoFarmer BlackJack Worker is already running! Use `.bjstop` first.")
        self.bot.log("SYS", "[START] Initializing blackjack farm...")
        balance = await fetch_owo_balance(ctx)
        if balance is None:
            return await ctx.send("Failed to fetch owo cash balance.")
        data["starting_balance"] = balance
        data["current_balance"] = balance
        data["start_timestamp"] = datetime.now().isoformat()
        data["wins"] = 0
        data["losses"] = 0
        data["ties"] = 0
        data["commands_used"] = 0
        data["seq_index"] = 0
        data["internal_profit"] = 0
        save_data(data)
        self.bot.log("SYS", f"[START] Balance saved: {balance:,}")
        await ctx.send(f"A2OwoFarmer BlackJack Farm Running. Starting balance: __{balance:,}__ cowoncy.")
        farm_task = asyncio.create_task(run_farm(ctx))

    @commands.command()
    async def bjstop(self, ctx):
        global farming_active, data
        if not farming_active:
            return await ctx.send("A2OwoFarmer BlackJack Worker is not running.")
        farming_active = False
        data["timer_end"] = None
        save_data(data)
        await ctx.send("Stopped successfully. Timer also cleared if active.")
        self.bot.log("SYS", "[STOP] User halted farm.")

    @commands.command()
    async def bjtimer(self, ctx, *, time_input=None):
        global data
        if not time_input:
            return await ctx.send("Usage: `.bjtimer 1h 30m 20s`, `.bjtimer 45m`, etc.")
        seconds = parse_time_to_seconds(time_input)
        if seconds < 300:
            return await ctx.send("Error: Minimum timer duration allowed is 5 minutes.")
        data["timer_end"] = time.time() + seconds
        save_data(data)
        await ctx.send(f"Timer set for **{time_input}**. Farm will stop after winning.")

    @commands.command()
    async def bjstoponloss(self, ctx, amount_str=None):
        global data
        if not amount_str:
            return await ctx.send("Usage: `.bjstoponloss 100k`, `.bjstoponloss 1m`, `.bjstoponloss 500k`")
        try:
            limit = parse_amount(amount_str)
            if limit < 100000:
                return await ctx.send("Error: Minimum stop on loss amount allowed is 100k.")
            data["stop_on_loss_limit"] = limit
            save_data(data)
            await ctx.send(f"Stop on Loss limit set to **__{limit:,}__** cowoncy.")
        except Exception:
            await ctx.send("Invalid format! Use formats like `500k`, `1m`, `100k`, etc.")

    @commands.command(aliases=["h"])
    async def bjhelp(self, ctx):
        text = """
    # A2OwoFarmer BlackJack Farm
Prefix: `.`

__Main__
 Start: Starts The AutoBot
 Stop: Stops The AutoBot
 Status: Shows Bot Status
 Bets: Change bet sequence (Low/High)
 Timer: Set duration to auto-stop (.bjtimer 45m)
 StopOnLoss: Set max loss limit (.bjstoponloss 1m)

__Features__
 Auto Detects OwO Warnings
 Auto Cut After 1 Warning
 Auto Determine Hit/Stand
 Tracking & Profit Calculator
 Smart Dynamic Betting
 Integrated Data with Advanced Decisions

__Made by Ayush Rajdev & Anzar Iqbal__"""
        await ctx.send(text)

    @commands.command()
    async def bjbets(self, ctx, seq_name=None):
        cfg = load_config()
        if not seq_name:
            current = cfg.get("BET_SEQUENCE", "Low")
            return await ctx.send(f"Usage: `.bjbets Low` or `.bjbets High`\nCurrent: {current}")
        target = seq_name.capitalize()
        if target not in BET_SEQUENCES:
            return await ctx.send("Invalid sequence. Use `Low` or `High`.")
        cfg["BET_SEQUENCE"] = target
        with open("config.json", "w") as f:
            json.dump(cfg, f, indent=2)
        await ctx.send(f"Sequence updated to **__{target}__**. Applies on win/restart.")

    @commands.command()
    async def bjstatus(self, ctx):
        global data
        balance = await fetch_owo_balance(ctx)
        if balance is not None:
            data["current_balance"] = balance
            save_data(data)
            self.bot.log("SYS", f"[STATUS] Current balance updated: {balance:,}")
        else:
            self.bot.log("SYS", "[STATUS] Could not fetch balance, using saved value")
        profit = data["current_balance"] - data["starting_balance"]
        profit_str = f"+{profit:,}" if profit >= 0 else f"{profit:,}"
        status_icon = "\U0001f7e2" if profit >= 0 else "\U0001f534"
        total_games = data["wins"] + data["losses"] + data["ties"]
        win_pct = (data["wins"] / total_games * 100) if total_games > 0 else 0.0
        loss_pct = (data["losses"] / total_games * 100) if total_games > 0 else 0.0
        start_dt = datetime.fromisoformat(data["start_timestamp"]) if data["start_timestamp"] else datetime.now()
        elapsed = datetime.now() - start_dt
        h, rem = divmod(int(elapsed.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        cfg = load_config()
        text = (
            f"**A2OwoFarmer BLACKJACK FARM STATUS**\n\n"
            f"{status_icon} Balance: Started __{data['starting_balance']:,}__ | Current __{data['current_balance']:,}__\n"
            f"Profit/Loss: __{profit_str}__\n\n"
            f"Results: Wins __{data['wins']}__ ({win_pct:.1f}%) | Losses __{data['losses']}__ ({loss_pct:.1f}%) | Ties __{data['ties']}__\n\n"
            f"Runtime: Started __{start_dt.strftime('%H:%M %m/%d')}__ | Elapsed __{h}h {m}m {s}s__\n\n"
            f"Config: Sequence __{cfg.get('BET_SEQUENCE', 'Low')}__ | Index __{data.get('seq_index', 0)}__ | Commands __{data['commands_used']}__"
        )
        await ctx.send(text)

async def setup(bot):
    cog = BlackjackFarm(bot)
    await bot.add_cog(cog)

def run_standalone(token):
    print(f"{Fore.CYAN}")
    print("  A2 OWO FARMER - Blackjack Farm Standalone")
    print(f"  Made by Ayush Rajdev & Anzar Iqbal{Style.RESET_ALL}")
    print()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ghosty = commands.Bot(command_prefix=".", case_insensitive=True, self_bot=True, intents=discord.Intents.all())
    ghosty.remove_command("help")

    @ghosty.event
    async def on_ready():
        print(f"{Fore.LIGHTRED_EX} > A2OwoFarmer BlackJack Farm Connected To:{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{ghosty.user}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTRED_EX} > Made by Ayush Rajdev & Anzar Iqbal{Style.RESET_ALL}")

    farming_active_local = [False]
    config = load_config()

    @ghosty.command()
    async def start(ctx):
        nonlocal farming_active_local
        global farming_active, data
        if farming_active_local[0]:
            return await ctx.send("Already running! Use `.stop` first.")
        farming_active_local[0] = True
        farming_active = True
        balance = await fetch_owo_balance(ctx)
        if balance is None:
            farming_active_local[0] = False
            farming_active = False
            return await ctx.send("Failed to fetch balance.")
        data["starting_balance"] = balance
        data["current_balance"] = balance
        data["start_timestamp"] = datetime.now().isoformat()
        data["wins"] = 0
        data["losses"] = 0
        data["ties"] = 0
        data["commands_used"] = 0
        data["seq_index"] = 0
        data["internal_profit"] = 0
        save_data(data)
        await ctx.send(f"A2OwoFarmer BlackJack Farm Running. Starting balance: __{balance:,}__ cowoncy.")
        asyncio.create_task(run_farm(ctx))

    @ghosty.command()
    async def stop(ctx):
        nonlocal farming_active_local
        global farming_active, data
        if not farming_active_local[0]:
            return await ctx.send("Not running.")
        farming_active_local[0] = False
        farming_active = False
        data["timer_end"] = None
        save_data(data)
        await ctx.send("Stopped.")

    @ghosty.command()
    async def timer(ctx, *, time_input=None):
        global data
        if not time_input:
            return await ctx.send("Usage: `.timer 1h 30m 20s`")
        seconds = parse_time_to_seconds(time_input)
        if seconds < 300:
            return await ctx.send("Minimum: 5 minutes.")
        data["timer_end"] = time.time() + seconds
        save_data(data)
        await ctx.send(f"Timer set for {time_input}.")

    @ghosty.command()
    async def stoponloss(ctx, amount_str=None):
        global data
        if not amount_str:
            return await ctx.send("Usage: `.stoponloss 100k`")
        try:
            limit = parse_amount(amount_str)
            if limit < 100000:
                return await ctx.send("Minimum: 100k.")
            data["stop_on_loss_limit"] = limit
            save_data(data)
            await ctx.send(f"Stop on Loss set to {limit:,}.")
        except Exception:
            await ctx.send("Invalid format.")

    @ghosty.command(aliases=["h"])
    async def help(ctx):
        await ctx.send("A2OwoFarmer BlackJack Farm - Prefix: `.` | Commands: start, stop, timer, stoponloss, bets, status")

    @ghosty.command()
    async def bets(ctx, seq_name=None):
        cfg = load_config()
        if not seq_name:
            return await ctx.send(f"Current: {cfg.get('BET_SEQUENCE', 'Low')}")
        target = seq_name.capitalize()
        if target not in BET_SEQUENCES:
            return await ctx.send("Use Low or High.")
        cfg["BET_SEQUENCE"] = target
        with open("config.json", "w") as f:
            json.dump(cfg, f, indent=2)
        await ctx.send(f"Updated to {target}.")

    @ghosty.command()
    async def status(ctx):
        global data
        balance = await fetch_owo_balance(ctx)
        if balance is not None:
            data["current_balance"] = balance
            save_data(data)
        profit = data["current_balance"] - data["starting_balance"]
        profit_str = f"+{profit:,}" if profit >= 0 else f"{profit:,}"
        total_games = data["wins"] + data["losses"] + data["ties"]
        win_pct = (data["wins"] / total_games * 100) if total_games > 0 else 0.0
        start_dt = datetime.fromisoformat(data["start_timestamp"]) if data["start_timestamp"] else datetime.now()
        elapsed = datetime.now() - start_dt
        h, rem = divmod(int(elapsed.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        cfg = load_config()
        text = (
            f"**A2OwoFarmer BLACKJACK FARM STATUS**\n"
            f"Balance: {data['starting_balance']:,} -> {data['current_balance']:,} ({profit_str})\n"
            f"Wins: {data['wins']} ({win_pct:.1f}%) | Losses: {data['losses']} | Ties: {data['ties']}\n"
            f"Elapsed: {h}h {m}m {s}s | Sequence: {cfg.get('BET_SEQUENCE', 'Low')}"
        )
        await ctx.send(text)

    ghosty.run(token)

if __name__ == "__main__":
    config = load_config()
    if not os.path.exists("config.json") or not config.get("TOKEN"):
        print(f"{Fore.RED}Missing config.json or TOKEN.{Style.RESET_ALL}")
        exit(1)
    run_standalone(config["TOKEN"])
