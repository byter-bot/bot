import io

import discord
from discord.ext import commands


class Admin(commands.Cog, command_attrs={"hidden": True}):
    def __init__(self, bot):
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


def setup(bot):
    bot.add_cog(Admin(bot))