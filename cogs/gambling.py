# A2 OWO FARMER - Combined OwO Bot Suite
# Made by Ayush Rajdev & Anzar Iqbal

import asyncio
import time
import random
import core.state as state
from discord.ext import commands

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = True
        self.task = None
        
    def trigger_coinflip(self):
        cfg = self.bot.config.get('commands', {}).get('coinflip', {})
        amount = cfg.get('amount', 1)
        side = cfg.get('side', 'h')
        
        self.bot.cmd_states['coinflip']['content'] = f"cf {side} {amount}"
        self.bot.cmd_states['coinflip']['delay'] = random.uniform(30, 60)
        state.stats['coinflip_count'] = state.stats.get('coinflip_count', 0) + 1

    def trigger_slots(self):
        cfg = self.bot.config.get('commands', {}).get('slots', {})
        amount = cfg.get('amount', 1)
        
        self.bot.cmd_states['slots']['content'] = f"slots {amount}"
        self.bot.cmd_states['slots']['delay'] = random.uniform(25, 50)
        state.stats['slots_count'] = state.stats.get('slots_count', 0) + 1

    async def register_actions(self):
        cfg_cf = self.bot.config.get('commands', {}).get('coinflip', {})
        if cfg_cf.get('enabled', False):
            self.bot.log("SYS", "Gambling (Coinflip) Module configured.")
            await self.bot.neura_register_command("coinflip", "cf", priority=3, delay=random.uniform(30, 60), initial_offset=15)
            self.trigger_coinflip()

        cfg_slots = self.bot.config.get('commands', {}).get('slots', {})
        if cfg_slots.get('enabled', False):
            self.bot.log("SYS", "Gambling (Slots) Module configured.")
            await self.bot.neura_register_command("slots", "slots", priority=3, delay=random.uniform(25, 50), initial_offset=20)
            self.trigger_slots()

async def setup(bot):
    cog = Gambling(bot)
    await bot.add_cog(cog)