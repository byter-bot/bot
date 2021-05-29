import aiohttp
import discord
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop)

    @commands.command()
    async def cat(self, ctx):
        """cat"""
        resp = await self.session.get("https://api.thecatapi.com/v1/images/search")
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
