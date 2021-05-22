import asyncio
import contextlib
import concurrent.futures
import io
import textwrap
import traceback
import threading
import time

import discord
from discord.ext import commands
import sys


codeblock_wrapper = textwrap.TextWrapper(
    width=1000, max_lines=32, placeholder='…',
    initial_indent='```py\n', break_on_hyphens=False,
    replace_whitespace=False, drop_whitespace=False
)

def format_codeblock(text: str) -> str:
    if text == '':
        return '```<empty>```'

    formatted = codeblock_wrapper.fill(str(text))

    if len(formatted) > 1024:
        formatted = formatted[:1024] + '…'

    formatted = formatted + '\n```'

    return formatted

class Admin(commands.Cog, command_attrs={"hidden": True}):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def cog_check(self, ctx):
        return self.bot.is_owner(ctx.author)

    @commands.command()
    async def doc(self, ctx, obj: str):
        """Returns __doc__ for given object"""
        try:
            doc = (__builtins__|globals()|locals())[obj.split('.')[0]]

        except KeyError:
            await ctx.send(f'Obj {obj} not found!')
            return

        for i in obj.split('.')[1:]:
            try:
                doc = getattr(doc, i)

            except AttributeError:
                await ctx.send(f'Attribute {i} does not exist!')
                return

        doc = doc.__doc__

        await ctx.send(file=discord.File(io.StringIO(doc),'a.py'))

    @commands.command()
    async def eval(self, ctx, *, code: str):
        if code.startswith('```'):
            code = '\n'.join(code.splitlines()[1:-1])

        else:
            code = f"return {code.strip('` ')}"

        code = 'async def func():\n' + textwrap.indent(code, '  ')
        code_return = '<empty>'
        code_stdout = io.BytesIO()
        env = {**globals()|locals()}

        try:
            exec(code, env)
            with contextlib.redirect_stdout(code_stdout):
                code_return = await env['func']()

        except Exception as exc:
            stdout_formatted = format_codeblock(code_stdout.getvalue().decode())
            traceback_formatted = format_codeblock(traceback.format_exc(-1))
            return_formatted = textwrap.shorten(str(code_return), width=36, placeholder='…')
            await ctx.send(
                embed=discord.Embed(
                    color=0xfa5050,
                    title=f":x: {exc}!",
                    description=f"Return → `{return_formatted}` "
                ).add_field(
                    name='Stdout', value=stdout_formatted, inline=False
                ).add_field(
                    name='Traceback', value=traceback_formatted, inline=False
                )
            )

        else:
            stdout_formatted = format_codeblock(code_stdout.getvalue().decode())
            return_formatted = textwrap.shorten(str(code_return), width=36, placeholder='…')
            await ctx.send(
                embed=discord.Embed(
                    color=0x50fa50,
                    title=f":white_check_mark: Code evaluated",
                    description=f"Return → `{return_formatted}` "
                ).add_field(
                    name='Stdout', value=stdout_formatted, inline=False
                )
            )



def setup(bot):
    bot.add_cog(Admin(bot))