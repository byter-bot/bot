import datetime
import random
import time

import discord
import psutil
from discord.ext import commands, tasks


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.commands_completed = 0
        self.commands_errored = 0
        self.update_status.start()

    def cog_unload(self):
        self.update_status.cancel()

    @tasks.loop(minutes=5)
    async def update_status(self):
        if random.randint(0, 25) == 15:
            await self.bot.change_presence(activity=random.choice([
                discord.Activity(
                    name=random.choice(['C418', 'Disasterpeace', 'Datassette', 'Lifeformed']),
                    type=discord.ActivityType.listening
                ),
                discord.Activity(
                    name=random.choice([
                        'C418 - surface pension', 'C418 - impostor syndrome', 'C418 - no pressure',
                        'C418 - buildup errors', 'C418 - total drag', "C418 - this doesn't work"
                    ]),
                    type=discord.ActivityType.listening
                ),
                discord.Game(
                    name='at /dev/' + random.choice(['tty', 'sda', 'mem', 'loop0', 'cpu', 'null'])
                ),
                discord.Game(name='did you know? this status only exists <1% of the time'),
                None
            ]))
            return

        await self.bot.change_presence(activity=random.choice([
            discord.Game(name=f'at {len(self.bot.guilds)} servers!'),
            discord.Activity(
                name=f'for {self.bot.config["prefix"][0]}help',
                type=discord.ActivityType.watching
            ),
            discord.Activity(
                name=(
                    'discord for ' + str(int(
                        (datetime.datetime.now().timestamp() - psutil.Process().create_time())
                        / 3600
                    )) + ' hours!'
                ),
                type=discord.ActivityType.watching
            )
        ]))

    @update_status.before_loop
    async def before_update_status(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_command_completion(self, *_):
        self.commands_completed += 1

    @commands.Cog.listener()
    async def on_command_error(self, *_):
        self.commands_errored += 1

    @commands.command()
    async def stats(self, ctx: commands.Context):
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

        proc_info = psutil.Process().as_dict(attrs=['cpu_percent', 'memory_percent', 'create_time'])
        bot_uptime = datetime.timedelta(seconds=time.time()-proc_info['create_time'])
        bot_uptime = str(bot_uptime).split('.')[0]
        embed.add_field(
            name='Bot',
            value=(
                f'Ws latency: {self.bot.latency*1000:.0f}ms\n'
                f'Cached messages: {len(self.bot.cached_messages)}\n'
                f'CPU: {proc_info["cpu_percent"]:.2f}%\n'
                f'RAM: {proc_info["memory_percent"]:.2f}%\n'
                f'Uptime: {bot_uptime}'
            )
        )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Stats(bot))
