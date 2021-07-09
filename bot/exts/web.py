import aiohttp
import html
import re
import typing
import urllib.parse

import discord
from discord.ext import commands


class Web(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['wiki'])
    async def wikipedia(self, ctx, limit: typing.Optional[int] = 4, *, query: str):
        """Searches wikipedia

        You may optionally provide a limit for the results before the query (defaults to 4)"""
        if not 1 <= limit <= 25:
            raise commands.BadArgument('search limit must be between 1 and 25')

        async with aiohttp.ClientSession(loop=self.bot.loop) as session:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srprop': 'snippet',
                'srsearch': query,
                'srlimit': limit
            }
            async with session.get('https://en.wikipedia.org/w/api.php', params=params) as resp:
                if not resp.ok:
                    await ctx.send('An error occured querying data')
                    return

                data = (await resp.json())['query']['search']
                embed = discord.Embed(
                    color=0x5050fa,
                    title=f'Wikipedia results for "{query}"'
                )

                for index, obj in enumerate(data):
                    desc = html.unescape(re.sub(r'<.*?>', '', obj['snippet']))[:256] + '… '
                    link = f'[link](https://wikipedia.org/wiki/{urllib.parse.quote(obj["title"])})'
                    embed.add_field(
                        name=f'{index+1}: {obj["title"]}',
                        value=desc + link,
                        inline=False
                    )

                if limit < 10:
                    await ctx.send(embed=embed)

                else:
                    await ctx.author.send(embed=embed)
                    await ctx.message.add_reaction('\N{white heavy check mark}')


def setup(bot):
    bot.add_cog(Web(bot))
