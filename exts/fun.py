import aiohttp
import discord
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild.id == self.bot.config['main_guild_id']:
            return

        filtered_msg = ''.join(
            char for char in message.content.lower() if 'a' <= char <= 'z' or char == ' '
        )

        for reaction, triggers in self.bot.config['reactions'].items():
            for trigger in triggers:
                if trigger in filtered_msg.split(' '):
                    if reaction.isdecimal:
                        reaction = self.bot.get_emoji(int(reaction))

                    await message.add_reaction(reaction)
                    break

    @commands.command()
    async def cat(self, ctx):
        """cat"""
        async with aiohttp.ClientSession(loop=self.bot.loop) as session:
            resp = await session.get("https://api.thecatapi.com/v1/images/search")
            if resp.ok:
                json = await resp.json()
                url = json[0]['url']
                await ctx.send(
                    embed=discord.Embed(
                        color=0x5050fa,
                        title='Cat!!'
                    ).set_image(url=url)
                )

            else:
                await ctx.send("Couldn't get a cat image <:creustickersad:726924232461910077>")


def setup(bot):
    bot.add_cog(Fun(bot))
