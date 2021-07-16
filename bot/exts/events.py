import io
import secrets

import discord
from discord.ext import commands


class QaSession:
    """Object storing questions in events with an Q&A"""
    def __init__(self):
        self.questions = []
        self.seen = []
        self.is_open = False

    @property
    def is_closed(self):
        return not self.is_open

    def pick_random(self):
        obj = self.questions.pop(secrets.randbelow(len(self.questions)))
        self.seen.append(obj)
        return obj

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False
        dump = (self.questions, self.seen)
        self.questions = []
        self.seen = []
        return dump

    def __len__(self):
        return len(self.questions) + len(self.seen)


class Events(commands.Cog, command_attrs={'hidden': True}):
    def __init__(self, bot):
        self.bot = bot
        self.qa_session = QaSession()

    def cog_check(self, ctx):
        return ctx.guild.id == self.bot.config['main_guild_id']

    @commands.command()
    async def qa(self, ctx, *, question):
        if self.qa_session.is_closed:
            raise commands.CheckFailure("There isn't an qa session running")

        self.qa_session.questions.append((ctx.author, question, ctx.message))
        await ctx.message.add_reaction('\N{white heavy check mark}')

    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_any_role('Créu Chief', 'Créu Crew'))
    async def qastart(self, ctx):
        if self.qa_session.is_open:
            raise commands.CheckFailure('An qa session is already running')

        self.qa_session.open()
        await ctx.message.add_reaction('\N{white heavy check mark}')

    @commands.command()
    @commands.check_any(commands.is_owner(), commands.has_any_role('Créu Chief', 'Créu Crew'))
    async def qaend(self, ctx):
        if self.qa_session.is_closed:
            raise commands.CheckFailure("There isn't an qa session running")

        questions, seen = self.qa_session.close()
        await ctx.message.add_reaction('\N{white heavy check mark}')

        content = io.StringIO(
            '\n'.join([
                f'Remaining ({len(questions)}):',
                *(
                    f'From: {author} ({author.id})\n{question}\nUrl: {msg.jump_url}\n'
                    for author, question, msg in questions
                ),
                f'Seen ({len(seen)}):',
                *(
                    f'From: {author} ({author.id})\n{question}\nUrl: {msg.jump_url}\n'
                    for author, question, msg in seen
                )
            ])
        )

        await ctx.send(file=discord.File(content, 'qa.txt'))

    @commands.command(aliases=['qapick'])
    @commands.check_any(
        commands.is_owner(),
        commands.has_any_role('Créu Chief', 'Créu Curator', 'Créu Captain')
    )
    async def qpick(self, ctx):
        if self.qa_session.is_closed:
            raise commands.CheckFailure("There isn't an qa session running")

        if len(self.qa_session.questions) == 0:
            await ctx.send('No questions left!')
            return

        author, question, message = self.qa_session.pick_random()
        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title=f'Question {len(self.qa_session.questions)} of {len(self.qa_session)}',
                description=f'{question}\n[Jump to message]({message.jump_url})',
                timestamp=message.created_at
            ).set_author(name=author, icon_url=author.avatar_url)
        )


def setup(bot):
    bot.add_cog(Events(bot))
