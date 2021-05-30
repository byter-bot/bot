import io
import json
import random

import discord
from discord.ext import commands


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def qa(self, ctx, *, question):
        if not hasattr(self, 'qa_questions'):
            raise commands.CheckFailure("There isn't an qa session running")

        self.qa_questions.append((ctx.author, question, ctx.message))
        await ctx.message.add_reaction('\N{white heavy check mark}')

    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_any_role('Créu Chief', 'Créu Crew'))
    async def qastart(self, ctx):
        if hasattr(self, 'qa_questions'):
            raise commands.CheckFailure('An qa session is already running!')

        self.qa_questions = []
        self.qa_questions_seen = []
        await ctx.message.add_reaction('\N{white heavy check mark}')

    @commands.command()
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

    @commands.command(aliases=['qapick'])
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


def setup(bot):
    bot.add_cog(Utils(bot))
