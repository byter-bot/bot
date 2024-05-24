import json
import re
import typing

import discord
from discord.ext import commands


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['emb'])
    @commands.has_permissions(manage_messages=True)
    async def embed(self, ctx, color: typing.Optional[discord.Color], title, *, description):
        """Generates an embed with color, title and description

        If color is omitted then it defaults to #5050fa"""
        if color is None:
            color = 0x5050fa

        await ctx.send(embed=discord.Embed(color=color, title=title, description=description))

    @commands.command(aliases=['remb'])
    @commands.has_permissions(manage_messages=True)
    async def embedraw(self, ctx, *, data: str):
        try:
            if not data.startswith('{') and not data.endswith('}'):
                data = '{' + data + '}'

            embed = discord.Embed.from_dict(json.loads(data))
            await ctx.send(embed=embed)

        except json.JSONDecodeError as error:
            await ctx.send(
                embed=discord.Embed(
                    color=0xfa5050,
                    title='Decode error!',
                    description=f'Something went wrong parsing the JSON\n`{error!r}`'
                )
            )

    @commands.command()
    async def poll(self, ctx, *, poll: str):
        """Create a poll

        A poll consists of title, optional description and options,
        · title is separated by a question mark or a comma
        · the description is put after the title and a semicolon
        · options are split by commas
        · options may be omitted and will be replaced with thumbs up/down
        · you may use a custom emoji in an option by placing it before a colon"""
        if '?' in poll and ';' not in poll and poll.index('?') != len(poll) - 1:
            title, poll = poll.split('?', 1)
            title += '?'

        elif ',' in poll:
            title, poll = poll.split(',', 1)

        else:
            title = poll
            description = ''
            if ';' in title:
                title, description = title.split(';', 1)
                description += '\n\n'

            embed = discord.Embed(
                color=0x5050fa,
                title=title.strip(),
                timestamp=ctx.message.created_at,
                description=(
                    description
                    + '<:hand_thumbsup:757023230073634922> / <:hand_thumbsdown:757019524058054686>'
                )
            )

            embed.set_author(name=f'Poll by {ctx.author}', icon_url=ctx.author.avatar_url)
            embed.set_footer(text=f'{ctx.prefix}poll')
            message = await ctx.send(embed=embed)
            try:
                await message.add_reaction(self.bot.get_emoji(757023230073634922))
                await message.add_reaction(self.bot.get_emoji(757019524058054686))

            except discord.InvalidArgument:
                pass

            return

        description = ''
        if ';' in poll:
            description, poll = poll.split(';', 1)
            description += '\n\n'

        elif ';' in title:
            title, description = title.split(';', 1)
            description += '\n\n'

        poll = [
            re.match(r'(<:.*:\d*>|[^:]*):(.*)', opt.strip()).groups()
            if ':' in opt else (chr(0x1f1e6 + index), opt.strip())
            for index, opt in enumerate(poll.split(','))
        ]

        if len(poll) > 20:
            raise commands.TooManyArguments('too many poll options (> 20)')

        embed = discord.Embed(
            color=0x5050fa,
            title=title.strip(),
            timestamp=ctx.message.created_at,
            description=description + '\n'.join(f'{emote}: {text}' for emote, text in poll)
        )

        embed.set_author(name=f'Poll by {ctx.author}', icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f'{ctx.prefix}poll')

        message = await ctx.send(embed=embed)
        for emote, _ in poll:
            try:
                await message.add_reaction(emote.strip())

            except discord.NotFound:
                pass


def setup(bot):
    bot.add_cog(Utils(bot))
