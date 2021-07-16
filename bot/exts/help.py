import itertools
from typing import List, Mapping, Optional

import discord
from discord.ext import commands


class EmbedHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]):
        ctx: commands.Context = self.context
        bot: commands.Bot = ctx.bot
        embed = discord.Embed(
            color=0x5050fa,
            title='Hey there!',
            description=(
                'Below are all available commands on their respective categories\n'
                'You can run this command + a command or category to see more info on it!\n'
                "There's also a documentation website right [here](https://docs.byterbot.com)"
            )
        )

        def get_category(command: commands.Command) -> str:
            if command.cog:
                return command.cog.qualified_name

            return 'No category'

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        for category, cmds in itertools.groupby(filtered, key=get_category):
            if len(embed.fields) >= 25:
                await ctx.author.send(embed=embed)
                embed = discord.Embed(color=0x5050fa)

            embed.add_field(
                name=category,
                value=', '.join(map(str, sorted(cmds, key=lambda c: c.name))),
                inline=False
            )

        if embed:
            await ctx.author.send(embed=embed)

        await ctx.message.add_reaction('\N{white heavy check mark}')

    async def send_cog_help(self, cog: commands.Cog):
        embed = discord.Embed(title=cog.qualified_name, color=0x5050fa)
        if cog.description:
            embed.description = cog.description

        embed.add_field(
            name='Commands',
            value='\n'.join(f'**{cmd}** - {cmd.short_doc}' for cmd in cog.walk_commands())
        )

        await self.context.send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        ctx: commands.Context = self.context
        embed = discord.Embed(
            color=0x5050fa,
            title=command.name,
            description=command.help or ''
        )
        if not command.hidden:
            embed.description += f'\n\n[Documentation](https://docs.byterbot.com/#/?id={command})'

        if not command.can_run(ctx):
            embed.description += '\n\n:warning: You do not seem to be able to run this command here'

        embed.add_field(
            name='Category',
            value=command.cog.qualified_name if command.cog else 'No category'
        )

        embed.add_field(
            name='Aliases',
            value=', '.join(f'`{i}`' for i in command.aliases) or 'None'
        )

        embed.add_field(
            name='Arguments',
            value=', '.join(f'`{i}`' for i in command.signature.strip().split()) or 'None'
        )

        await ctx.send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        ctx: commands.Context = self.context
        embed = discord.Embed(
            color=0x5050fa,
            title=group.name,
            description=group.help or ''
        )
        if not group.hidden:
            embed.description += f'\n\n[Documentation](https://docs.byterbot.com/#/?id={group})'

        if not group.can_run(ctx):
            embed.description += '\n\n:warning: You do not seem to be able to run this command here'

        embed.add_field(
            name='Subcommands',
            value=', '.join(f'**{cmd}** - {cmd.short_doc}' for cmd in group.commands)
        )

        embed.add_field(
            name='Category',
            value=group.cog.qualified_name if group.cog else 'No category'
        )

        embed.add_field(
            name='Aliases',
            value=', '.join(f'`{i}`' for i in group.aliases) or 'None'
        )

        embed.add_field(
            name='Arguments',
            value=', '.join(f'`{i}`' for i in group.signature.split()) or 'None'
        )

        await ctx.send(embed=embed)


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.help_command = EmbedHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = commands.DefaultHelpCommand()

    @commands.command(name='commands')
    async def _commands(self, ctx: commands.Context):
        """Lists available commands"""
        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title='Available commands:',
                description=', '.join(
                    f'`{cmd}`' for cmd in self.bot.walk_commands()
                    if not cmd.hidden and cmd.can_run(ctx)
                )
            )
        )

    @commands.command()
    async def prefix(self, ctx: commands.Context):
        """Shows the bot's prefix"""
        prefix = self.bot.config['prefix']
        if len(prefix) > 1:
            await ctx.send('Hey! My prefixes are ' + ', '.join(f'`{i}`' for i in prefix) + '!')
        if len(prefix) == 0:
            await ctx.send('Hey! No prefixes are set, but you can ping me!')
        else:
            await ctx.send(f'Hey! My prefix is `{prefix[0]}`!')


def setup(bot):
    bot.add_cog(Help(bot))
