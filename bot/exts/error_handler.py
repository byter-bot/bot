import datetime
import hashlib
import io
import json
import re
import traceback

import fuzzywuzzy.fuzz
import fuzzywuzzy.process
import discord
from discord.ext import commands, tasks


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.error_log_channel = bot.config['error_channel_id']
        self.clean_logs.start()

    def cog_unload(self):
        self.clean_logs.cancel()

    @tasks.loop(hours=5)
    async def clean_logs(self):
        before = datetime.datetime.now() - datetime.timedelta(days=2)
        async for log in self.bot.get_channel(self.error_log_channel).history(before=before):
            await log.delete()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            suggestion = fuzzywuzzy.process.extractOne(
                ctx.invoked_with, self.bot.commands,
                scorer=fuzzywuzzy.fuzz.WRatio, score_cutoff=70
            )
            if suggestion:
                await ctx.send(
                    f'Command {ctx.invoked_with} not found, did you mean {suggestion[0]}?'
                )

        elif isinstance(error, commands.ConversionError):
            await ctx.send(error)

        elif isinstance(error, commands.UserInputError):
            formatted_error = re.sub(
                # Error Name ('error message') -> Error name: error message
                r" \(['\"](.*)['\"]\)", r': \1',
                # split PascalCase
                re.sub(r'([A-Z][a-z]+)', r'\1 ', repr(error))
            ).capitalize().strip('.')

            await ctx.send(
                embed=discord.Embed(
                    color=0xfa5050,
                    title=':x: Input error!',
                    description=formatted_error
                )
            )

        elif isinstance(error, commands.CheckFailure):
            await ctx.send(
                embed=discord.Embed(
                    color=0xfa5050,
                    title=':x: Check failed!',
                    description=f'{error}'
                )
            )

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send('That command is currently disabled')

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
            return

        else:
            formatted_error = str(error)
            if hasattr(error, 'original'):
                formatted_error = repr(error.original)

            if len(formatted_error) > 80:
                formatted_error = formatted_error[:80] + '…'

            await ctx.send(
                embed=discord.Embed(
                    color=0xfa5050,
                    title=":x: Uncaught error!",
                    description=(
                        "An uncaught error has occurred while processing your command:\n"
                        f"`{formatted_error}`\n\n"
                        "This has been automatically reported, feel free to open an issue on "
                        "[my server](https://discord.gg/ZKHjRcy9bd) (or at my "
                        "[github repo](https://github.com/dzshn/byter-rewrite/issues/new))"
                    )
                )
            )

            dump_obj = {
                "ctx": {
                    "content": ctx.message.content,
                    "args": [str(i) for i in ctx.args],
                    "kwargs": ctx.kwargs,
                    "perms": {
                        "guild": ctx.me.guild_permissions.value,
                        "channel": ctx.me.permissions_in(ctx.channel).value
                    }
                },
                "error": {
                    "str": str(error),
                    "repr": repr(error),
                    "attrs": {
                        attr: repr(getattr(error, attr))
                        for attr in dir(error) if not callable(getattr(error, attr))
                    }
                }
            }

            if hasattr(error, 'original'):
                dump_obj['traceback'] = traceback.format_exception(
                    type(error), error, error.__traceback__
                )

            if self.bot.error_log_channel:
                await self.bot.get_channel(self.error_log_channel).send(
                    f"{hashlib.md5(ctx.author.id.to_bytes(10,'big')).hexdigest()}:"
                    f"{hashlib.md5(ctx.message.id.to_bytes(10,'big')).hexdigest()} "
                    f"<@{self.bot.owner_id}>",
                    file=discord.File(io.StringIO(json.dumps(dump_obj, indent=4)), 'dump.json')
                )

            else:
                print(dump_obj)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
