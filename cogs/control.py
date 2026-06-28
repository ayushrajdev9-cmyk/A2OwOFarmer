# A2 OWO FARMER - Combined OwO Bot Suite
# Made by Ayush Rajdev & Anzar Iqbal

import asyncio
import time
from discord.ext import commands
from core import state

class Control(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if str(message.author.id) != str(self.bot.user_id):
            return
            
        content = message.content.lower().strip()
        
        if content == '.stop':
            if not self.bot.paused:
                self.bot.paused = True
                state.bot_paused = True
                self.bot.log("SYS", "Bot PAUSED via Chat cmd")
                
        elif content == '.start' or content == '.resume':
            if self.bot.paused:
                self.bot.paused = False
                state.bot_paused = False
                state.active_session_start = time.time()
                for bot in state.bot_instances:
                    bot.paused = False
                    bot.throttle_until = 0
                self.bot.log("SYS", "Bot RESUMED via Chat cmd")


        elif content == '.status':
            status = "PAUSED " if self.bot.paused else "RUNNING "

            uptime = time.time() - state.stats['uptime_start']
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            status += f"| Uptime: {hours}h {minutes}m"
            self.bot.log("SYS", status)

async def setup(bot):
    cog = Control(bot)
    await bot.add_cog(cog)