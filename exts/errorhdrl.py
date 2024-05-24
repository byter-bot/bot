import hashlib
import io
import json

import discord
from discord.ext import commands


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        dump_obj = {
            "error": {
                "str": str(error),
                "attrs": {
                    attr: str(getattr(error, attr))
                    for attr in error.__dir__()
                    if not attr.startswith('_')
                }
            },
            "ctx": {
                "message": {"content": ctx.message.content},
                "args": ctx.args,
                "kwargs": ctx.kwargs,
                "perms": {
                    "guild": ctx.me.guild_permissions.value,
                    "channel": ctx.me.permissions_in(ctx.channel).value
                }
            }
        }

        await self.bot.get_channel(845464282338295808).send(
            f"{hashlib.md5(ctx.author.id.to_bytes(10,'big')).hexdigest()}:"
            f"{hashlib.md5(ctx.message.id.to_bytes(10,'big')).hexdigest()}",
            file=discord.File(io.StringIO(json.dumps(dump_obj, indent=4)), 'dump.json')
        )


def setup(bot):
    bot.add_cog(ErrorHandler(bot))