# A2 OWO FARMER - Combined OwO Bot Suite
# Made by Ayush Rajdev & Anzar Iqbal

import asyncio
import time
import random
from discord.ext import commands

class ChannelSwitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = True
        self.task = None
        
    def trigger_switch(self):
        cfg = self.bot.config.get('utilities', {}).get('autochannel', {})
        interval_config = cfg.get('cooldown', [300, 350])
        
        if isinstance(interval_config, list) and len(interval_config) == 2:
            interval = random.uniform(interval_config[0], interval_config[1])
        else:
            interval = float(interval_config)
            
        if self.bot.is_busy:
            self.bot.log("SYS", "ChannelSwitch: Rotation delayed (Bot is busy).")
            return

        channels = self.bot.channels if (hasattr(self.bot, 'channels') and self.bot.channels) else cfg.get('channels', [])

        
        if len(channels) >= 2:
            current = str(self.bot.channel_id)
            available = [c for c in channels if str(c) != current]
            if available:
                next_chan = random.choice(available)
                self.bot.channel_id = int(next_chan)
                self.bot.log("SYS", f"ChannelSwitch: Rotated to channel {next_chan}")
        
        if 'channelswitch' in self.bot.cmd_states:
             self.bot.cmd_states['channelswitch']['delay'] = interval

    async def register_actions(self):
        cfg = self.bot.config.get('utilities', {}).get('autochannel', {})
        if cfg.get('enabled', False):
            self.bot.log("SYS", "ChannelSwitch Module configured.")
            interval_config = cfg.get('cooldown', [300, 350])
            if isinstance(interval_config, list) and len(interval_config) == 2:
                interval = random.uniform(interval_config[0], interval_config[1])
            else:
                interval = float(interval_config)

            await self.bot.neura_register_command("channelswitch", "", priority=5, delay=interval, initial_offset=10)

async def setup(bot):
    cog = ChannelSwitch(bot)
    await bot.add_cog(cog)
