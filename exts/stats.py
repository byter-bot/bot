import datetime
import platform
import time

import psutil
import discord
from discord.ext import commands


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.commands_completed = 0
        self.commands_errored = 0

    @commands.Cog.listener()
    async def on_command_completion(self, *_):
        self.commands_completed += 1

    @commands.Cog.listener()
    async def on_command_error(self, *_):
        self.commands_errored += 1

    @commands.command()
    async def stats(self, ctx):
        embed = discord.Embed(color=0x5070fa, title='Stats:')
        virt_mem = psutil.virtual_memory()
        sys_uptime = datetime.timedelta(seconds=time.time()-psutil.boot_time())
        sys_uptime = str(sys_uptime).split('.')[0]
        embed.add_field(
            name='System',
            value=(
                f'CPU: {psutil.cpu_percent()}% '
                f'(~{psutil.cpu_freq().current/1000:.2f}GHz)\n'
                f'RAM: {virt_mem.percent}% '
                f'({virt_mem.used/1024**3:.2f}/{virt_mem.total/1024**3:.2f}GiB)\n'
                f'Load average: {", ".join(map(str, psutil.getloadavg()))}\n'
                f'Uptime: {sys_uptime}'
            )
        )

        embed.add_field(
            name='Usage',
            value=(
                f'Commands completed: {self.commands_completed}\n'
                f'Commands errored: {self.commands_errored}\n'
                f'Total commands: {self.commands_completed + self.commands_errored}\n'
                f'Servers: {len(self.bot.guilds)}'
            )
        )

        proc_info = psutil.Process().as_dict(attrs=['cpu_percent', 'memory_percent'])
        embed.add_field(
            name='Bot',
            value=(
                f'Ws latency: {self.bot.latency*1000:.0f}ms\n'
                f'Cached messages: {len(self.bot.cached_messages)}\n'
                f'CPU: {proc_info["cpu_percent"]:.2f}%\n'
                f'RAM: {proc_info["memory_percent"]:.2f}%'
            )
        )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Stats(bot))
