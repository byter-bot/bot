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
                # Error Name ('error message.') -> Error name: error message
                r" \('(.*)\.'\)", r': \1',
                # split PascalCase
                re.sub(r'([A-Z][a-z]+)', r'\1 ', repr(error))
            ).capitalize()

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
                    description=f'{error.message}'
                )
            )

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send('That command is currently disabled')

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
            return

        else:
            if isinstance(error, commands.CommandInvokeError):
                await ctx.send(
                    embed=discord.Embed(
                        color=0xfa5050,
                        title=":x: Uncaught error!",
                        description=(
                            "An uncaught error has occurred while processing your command:\n"
                            f"`{error.original!r}`\n\n"
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

            await self.bot.get_channel(845464282338295808).send(
                f"{hashlib.md5(ctx.author.id.to_bytes(10,'big')).hexdigest()}:"
                f"{hashlib.md5(ctx.message.id.to_bytes(10,'big')).hexdigest()}",
                file=discord.File(io.StringIO(json.dumps(dump_obj, indent=4)), 'dump.json')
            )


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
