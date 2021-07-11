import asyncio
import contextlib
import io
import json
import pprint
import textwrap
import time
import traceback

import discord
from discord.ext import commands


def format_codeblock(content):
    if not str(content):
        return None

    formatted = pprint.pformat(content, width=51, compact=True)
    if len(formatted) > 1014:
        formatted = formatted[:1013] + '…'

    return f'```py\n{formatted}\n```'


def get_files(*contents):
    files = []
    for content in contents:
        if len(pprint.pformat(content, width=51, compact=True)) > 1014:
            files.append(discord.File(io.StringIO(pprint.pformat(content, width=128))))

    return files


class Admin(commands.Cog, command_attrs={"hidden": True}):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_eval_value = None

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
        env = {'_': self._last_eval_value, 'b': self.bot}
        env.update(globals())
        env.update(locals())
        try:
            exec_time = time.perf_counter()
            exec(code, env)
            with contextlib.redirect_stdout(code_stdout):
                code_return = await env['func']()

        except:  # noqa: E722
            return_formatted = format_codeblock(code_return)
            stdout_formatted = format_codeblock(code_stdout.getvalue())
            traceback_formatted = format_codeblock(traceback.format_exc(-1))
            embed = discord.Embed(
                color=0xfa5050,
                title=":x: error!",
                description=f"{(time.perf_counter()-exec_time)*1000:g}ms :clock2:"
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
                description=f"{(time.perf_counter()-exec_time)*1000:g}ms :clock2:"
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

            if code_return is not None:
                self._last_eval_value = code_return

    @commands.command(aliases=['h'])
    async def shell(self, ctx, *, command):
        command = '\n'.join(command.splitlines()[1:-1]) \
                    if command.startswith('```') \
                    else command.strip('` ')

        exec_time = time.perf_counter()
        proc = await asyncio.subprocess.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        stdout_formatted = format_codeblock(stdout.decode())
        stderr_formatted = format_codeblock(stderr.decode())
        if proc.returncode == 0:
            embed = discord.Embed(
                color=0x50fa50,
                title=':white_check_mark: Subprocess finished',
                description=f"{(time.perf_counter()-exec_time)*1000:g}ms :clock2:"
            )

        else:
            embed = discord.Embed(
                color=0xfa7050,
                title=f':x: Subprocess exited with returncode {proc.returncode}',
                description=f"{(time.perf_counter()-exec_time)*1000:g}ms :clock2:"
            )

        if stdout_formatted is None and stderr_formatted is None:
            embed.description = 'no output · ' + embed.description

        if stdout_formatted is not None:
            embed.add_field(name='Stdout:', value=stdout_formatted, inline=False)

        if stderr_formatted is not None:
            embed.add_field(name='Stderr:', value=stderr_formatted, inline=False)

        await ctx.send(embed=embed, files=get_files(stdout.decode(), stderr.decode()))

    @commands.command()
    async def reloadcfg(self, ctx):
        self.bot.config = json.load(open('config_defaults.json')) | json.load(open('config.json'))
        await ctx.message.add_reaction('\N{white heavy check mark}')

    @commands.command(aliases=['l'])
    async def loadexts(self, ctx, *exts):
        if len(exts) == 0:
            await ctx.send(', '.join(f'`{i}`' for i in self.bot.extensions.keys()))
            return

        errors = []
        for ext in exts:
            ext = f'bot.exts.{ext}' if not ext.startswith('bot.exts.') else f'{ext}'
            try:
                if ext in self.bot.extensions:
                    self.bot.reload_extension(ext)
                else:
                    self.bot.load_extension(ext)

            except Exception as exc:
                exc = repr(exc)
                if len(exc) > 200:
                    exc = exc[:200] + '…'

                errors.append(traceback.format_exc())

        if errors:
            await ctx.send(file=discord.File(io.StringIO('\n'.join(errors)), 'errors.py'))

        await ctx.message.add_reaction('\N{white heavy check mark}')


def setup(bot):
    bot.add_cog(Admin(bot))
