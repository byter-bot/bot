import contextlib
import io
import textwrap
import traceback
import time

import discord
from discord.ext import commands


codeblock_wrapper = textwrap.TextWrapper(
    width=1000, placeholder='…', initial_indent='```py\n',
    break_on_hyphens=False, replace_whitespace=False,
    drop_whitespace=False
)

def format_codeblock(text: str):
    text = str(text)
    if text == '':
        return None

    formatted = codeblock_wrapper.fill(str(text))
    if len(formatted) > 1000:
        formatted = formatted[:1000] + '…'

    formatted = formatted + '\n```'

    return formatted

def get_files(*contents):
    files = []
    for text in map(str, contents):
        if text and len(codeblock_wrapper.fill(text)) > 1000:
            files.append(discord.File(io.StringIO(text), 'trunc.py'))

    return files


class Admin(commands.Cog, command_attrs={"hidden": True}):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def cog_check(self, ctx):
        return self.bot.is_owner(ctx.author)

    @commands.command(aliases=['.'])
    async def eval(self, ctx, *, code: str):
        if code.startswith('```'):
            code = '\n'.join(code.splitlines()[1:-1])

        else:
            code = f"return {code.strip('` ')}"

        code = 'async def func():\n' + textwrap.indent(code, '  ')
        code_return = '<empty>'
        code_stdout = io.StringIO()
        env = {**globals()|locals()}
        try:
            exec_time = time.perf_counter()
            exec(code, env)
            with contextlib.redirect_stdout(code_stdout):
                code_return = await env['func']()

        except Exception as exc:
            return_formatted = format_codeblock(code_return)
            stdout_formatted = format_codeblock(code_stdout.getvalue())
            traceback_formatted = format_codeblock(traceback.format_exc(-1))
            embed = discord.Embed(
                color=0xfa5050,
                title=f":x: {exc!r}!",
                description=f"{time.perf_counter()-exec_time:3g}s :clock2:"
            )

            embed.add_field(name='Traceback', value=traceback_formatted, inline=False)
            embed.add_field(name='Return', value=return_formatted, inline=False)
            if stdout_formatted:
                embed.add_field(name='Stdout', value=stdout_formatted, inline=False)

            await ctx.send(
                embed=embed,
                files=get_files(code_return, code_stdout.getvalue(), traceback.format_exc(-1))
            )

        else:
            return_formatted = format_codeblock(code_return)
            stdout_formatted = format_codeblock(code_stdout.getvalue())
            embed = discord.Embed(
                color=0x50fa50,
                title=":white_check_mark: Code evaluated",
                description=f"{time.perf_counter()-exec_time:g}s :clock2:"
            )
            embed.add_field(
                name='Return', value=return_formatted, inline=False
            )

            if stdout_formatted:
                embed.add_field(
                    name='Stdout', value=stdout_formatted, inline=False
                )

            await ctx.send(
                embed=embed,
                files=get_files(code_return, code_stdout.getvalue())
            )


def setup(bot):
    bot.add_cog(Admin(bot))
