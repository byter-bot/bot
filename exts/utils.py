import io
import json
import random
import re

import discord
from discord.ext import commands


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def qa(self, ctx, *, question):
        if not hasattr(self, 'qa_questions'):
            raise commands.CheckFailure("There isn't an qa session running")

        self.qa_questions.append((ctx.author, question, ctx.message))
        await ctx.message.add_reaction('\N{white heavy check mark}')

    @commands.command(hidden=True)
    @commands.check_any(commands.is_owner(), commands.has_any_role('Créu Chief', 'Créu Crew'))
    async def qastart(self, ctx):
        if hasattr(self, 'qa_questions'):
            raise commands.CheckFailure('An qa session is already running!')

        self.qa_questions = []
        self.qa_questions_seen = []
        await ctx.message.add_reaction('\N{white heavy check mark}')

    @commands.command(hidden=True)
    @commands.check_any(commands.is_owner(), commands.has_any_role('Créu Chief', 'Créu Crew'))
    async def qaend(self, ctx):
        if not hasattr(self, 'qa_questions'):
            raise commands.CheckFailure("There isn't an qa session running")

        await ctx.send(
            file=discord.File(
                io.StringIO(
                    'Remaining questions:\n'
                    + '\n'.join(
                        f'From: {author} ({author.id})\nQuestion: {question}\nUrl: {msg.jump_url}\n'
                        for author, question, msg in self.qa_questions
                    )
                    + '\nQuestions seen:\n'
                    + '\n'.join(
                        f'From: {author} ({author.id})\nQuestion: {question}\nUrl: {msg.jump_url}\n'
                        for author, question, msg in self.qa_questions_seen
                    )
                ), 'qa.txt'
            )
        )

        delattr(self, 'qa_questions')
        delattr(self, 'qa_questions_seen')

    @commands.command(aliases=['qapick'], hidden=True)
    @commands.check_any(
        commands.is_owner(),
        commands.has_any_role('Créu Chief', 'Créu Curator', 'Créu Captain')
    )
    async def qpick(self, ctx):
        if not hasattr(self, 'qa_questions'):
            raise commands.CheckFailure("There isn't an qa session running")

        if len(self.qa_questions) == 0:
            await ctx.send('No questions left!')
            return

        n_question = random.randint(0, len(self.qa_questions) - 1)
        author, question, msg = self.qa_questions.pop(n_question)
        self.qa_questions_seen.append((author, question, msg))
        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title=(
                    'Question '
                    f'{n_question + 1}/{len(self.qa_questions) + len(self.qa_questions_seen)}'
                ),
                description=(
                    f'{question}\n'
                    f'[Jump to message]({msg.jump_url})'
                ),
                timestamp=msg.created_at
            ).set_author(name=author, icon_url=author.avatar_url)
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
                description=
                    description
                    + '<:hand_thumbsup:757023230073634922> / <:hand_thumbsdown:757019524058054686>'
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
            description=
                description
                + '\n'.join(f'{emote}: {text}' for emote, text in poll)
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
