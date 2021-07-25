import textwrap
import urllib.parse

import aiohttp
import discord
from discord.ext import commands


class Web(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['wiki'])
    async def wikipedia(self, ctx: commands.Context, *, query: str):
        """Searches wikipedia"""
        async with aiohttp.ClientSession(loop=self.bot.loop) as session:
            api_url = 'https://en.wikipedia.org/w/api.php'
            params_query = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srprop': 'snippet',
                'srsearch': query,
                'srlimit': 5
            }
            async with session.get(api_url, params=params_query) as resp:
                if not resp.ok:
                    await ctx.send('An error occured querying data')
                    return

                data_query = (await resp.json())['query']['search']

            if not data_query:
                await ctx.send(embed=discord.Embed(color=0xfa5050, title='No results!'))
                return

            params_parsed = {
                'action': 'query',
                'format': 'json',
                'prop': 'extracts',
                'exintro': 1,
                'explaintext': 1,
                'titles': '|'.join(i['title'] for i in data_query)
            }
            async with session.get(api_url, params=params_parsed) as resp:
                if not resp.ok:
                    await ctx.send('An error occured querying data')
                    return

                def match_title(x: dict) -> int:
                    for i, j in enumerate(data_query):
                        if j['title'] == x['title']:
                            return i

                data_parsed = (await resp.json())['query']['pages'].values()
                data_parsed = sorted(data_parsed, key=match_title)

            description = data_parsed[0]['extract']
            if len(description) > 1000:
                description = description[:999] + '…'

            description += (
                f' [link](https://wikipedia.org/wiki/{urllib.parse.quote(data_parsed[0]["title"])})'
            )

            embed = discord.Embed(color=0x5050fa, title=data_parsed[0]['title'], description=description)

            embed.set_footer(
                text='from wikipedia.org | 🄯 CC BY-SA 3.0',
                icon_url=(
                    'https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/'
                    'Wikipedia-logo-v2.svg/103px-Wikipedia-logo-v2.svg.png'
                )
            )

            if len(data_query) > 1:
                embed.add_field(
                    name='Other results',
                    value='\n'.join(
                        textwrap.shorten(
                            '[**{}**](https://wikipedia.org/wiki/{}) ─ {}'
                            .format(i['title'], urllib.parse.quote(i['title']), i['extract']),
                            width=180,
                            placeholder='…'
                        ) for i in data_parsed[1:]
                    ),
                    inline=False
                )

            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Web(bot))
