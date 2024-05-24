import contextlib
import datetime
import re
import time
import zoneinfo

import discord
import fuzzywuzzy.fuzz
import fuzzywuzzy.process
from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def time(self, ctx: commands.Context, *, timezone: str):
        """Gets current time in given timezone"""
        if re.fullmatch(r'(UTC|GMT)?[+-]?\d\d?:?(\d\d)?', timezone):
            if re.search(r'\d:?\d\d', timezone):
                offset = datetime.timedelta(
                    hours=int(re.findall(r'-?\d\d?(?=:?\d\d$)', timezone)[0]),
                    minutes=int(re.findall(r'-?', timezone)[0] + re.findall(r'\d\d$', timezone)[0])
                )

            else:
                offset = datetime.timedelta(hours=int(re.findall(r'-?\d+', timezone)[0]))

            if -1 <= offset.days >= 1:
                raise commands.BadArgument('Invalid offset (≥ 24 hrs)')

            dt = datetime.datetime.now(datetime.timezone(offset))
            offset_formmated = re.sub(r"(-?\d\d?):?(\d\d)$", r"\1:\2", timezone)
            if '-' not in timezone:
                offset_formmated = '+' + offset_formmated

            await ctx.send(
                embed=discord.Embed(
                    color=0x5050fa,
                    title=f'It is currently {dt.strftime("%H:%M")} for UTC{offset_formmated}',
                    description=(
                        f'**Zone:** {dt.tzname()}\n'
                        f'**Time:** {dt.strftime("%H:%M:%S")}\n'
                        f'**Date:** {dt.strftime("%A, %B %d, %Y")}\n'
                        f'**ISO timestamp:** {dt.isoformat()}'
                    )
                )
            )

        else:
            try:
                zone = zoneinfo.ZoneInfo(timezone)

            except zoneinfo.ZoneInfoNotFoundError:
                match_name = fuzzywuzzy.process.extractOne(
                    timezone, zoneinfo.available_timezones(),
                    scorer=fuzzywuzzy.fuzz.WRatio, score_cutoff=65
                )

                if match_name is None:
                    await ctx.send("I wasn't able to find a timezone with that name")
                    return

                zone = zoneinfo.ZoneInfo(match_name[0])

            dt = datetime.datetime.now(zone)
            dst = ''
            if dt.dst():
                dst = '**Daylight saving time offset:** ' \
                    + ('+' if abs(dt.dst()) == dt.dst() else '-') \
                    + str(dt.dst()).removesuffix(':00')

            zone_offset = '+' if abs(dt.utcoffset()) == dt.utcoffset() else '-' \
                + str(abs(dt.utcoffset())).removesuffix(':00')

            await ctx.send(
                embed=discord.Embed(
                    color=0x5050fa,
                    title=f'It is currently {dt.strftime("%H:%M")} there',
                    description=(
                        f'**Zone:** {zone.key.replace("_", " ")} ({dt.tzname()})\n'
                        f'**Offset:** {zone_offset}\n'
                        f'**Time:** {dt.strftime("%H:%M:%S")}\n'
                        f'**Date:** {dt.strftime("%A, %B %d, %Y")}\n'
                        f'**ISO timestamp:** {dt.isoformat()}\n'
                    ) + dst
                )
            )

    @commands.command(aliases=['?', 'whois'])
    @commands.cooldown(3, 10)
    async def whatis(self, ctx: commands.Context, obj_id: str):
        """Tries to fetch & gather info about an ID or object"""
        obj_id = int(''.join(i for i in obj_id if i.isdecimal()))
        with contextlib.suppress(discord.NotFound):
            member = await ctx.guild.fetch_member(obj_id)
            flags = [
                name.replace('_', ' ').capitalize()
                for name, val in iter(member.public_flags) if val
            ]
            if member.bot:
                flags.append('Bot')

            flags = ', '.join(flags)
            embed = discord.Embed(
                color=member.color.value,
                title=f'User (member): {member}',
                description=(
                    f'Top role: {member.top_role.mention} ({member.color})\n'
                    f'Other roles({len(member.roles)-2}): '
                    f'{", ".join(role.mention for role in member.roles[1:-1])}\n'
                    f'Joined at: {member.joined_at.strftime("%b %d, %Y (%H:%M:%S)")} '
                    f'({(datetime.datetime.utcnow() - member.joined_at).days} days ago)\n'
                    f'Created at: {member.created_at.strftime("%b %d, %Y (%H:%M:%S)")} '
                    f'({(datetime.datetime.utcnow() - member.created_at).days} days ago)\n'
                    f'Flags: {flags}\n\n'
                    f'[Avatar url]({member.avatar_url})'
                )
            )
            embed.set_thumbnail(url=member.avatar_url)
            await ctx.send(embed=embed)
            return

        with contextlib.suppress(discord.NotFound):
            user = await self.bot.fetch_user(obj_id)
            flags = [
                name.replace('_', ' ').capitalize()
                for name, val in iter(user.public_flags) if val
            ]
            if user.bot:
                flags.append('Bot')

            flags = ', '.join(flags)
            embed = discord.Embed(
                color=0x5050fa,
                title=f'User (external): {user}',
                description=(
                    f'Created at: {user.created_at.strftime("%b %d, %Y (%H:%M:%S)")} '
                    f'({(datetime.datetime.utcnow() - user.created_at).days} days ago)\n'
                    f'Flags: {flags}\n\n'
                    f'[Avatar url]({user.avatar_url})'
                )
            )
            embed.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=embed)
            return

        if (channel := self.bot.get_channel(obj_id)):
            embed = discord.Embed(color=0x5050fa)
            if isinstance(channel, discord.TextChannel):
                embed.title = f'Text channel: #{channel}'
                embed.description = (
                    f'Description: {channel.topic}\n'
                    f'Category: {channel.category} ({channel.category_id})\n'
                    f'Server: {channel.guild} ({channel.guild.id})\n'
                    f'Slowmode: {channel.slowmode_delay}s\n'
                    f'Created at: {channel.created_at.strftime("%b %d, %Y (%H:%M:%S)")} '
                    f'({(datetime.datetime.utcnow() - channel.created_at).days} days ago)\n'
                )

            elif isinstance(channel, discord.VoiceChannel):
                embed.title = f'Voice channel: {channel}'
                embed.description = (
                    f'Bitrate: {channel.bitrate/1000:.0f}kbps\n'
                    f'Region: {channel.rtc_region}\n'
                    f'User limit: {channel.user_limit}\n'
                    f'Category: {channel.category} ({channel.category_id})\n'
                    f'Server: {channel.guild} ({channel.guild.id})\n'
                    f'Created at: {channel.created_at.strftime("%b %d, %Y (%H:%M:%S)")} '
                    f'({(datetime.datetime.utcnow() - channel.created_at).days} days ago)\n'
                )

            elif isinstance(channel, discord.CategoryChannel):
                embed.title = f'Channel category: {channel}'
                embed.description = (
                    f'Server: {channel.guild} ({channel.guild.id})\n'
                    f'Created at: {channel.created_at.strftime("%b %d, %Y (%H:%M:%S)")} '
                    f'({(datetime.datetime.utcnow() - channel.created_at).days} days ago)\n'
                )

            elif isinstance(channel, discord.StageChannel):
                embed.title = f'Stage channel: #{channel}'
                embed.description = (
                    f'Description: {channel.topic}\n'
                    f'Bitrate: {channel.bitrate/1000:.0f}kbps\n'
                    f'Region: {channel.rtc_region}\n'
                    f'User limit: {channel.user_limit}\n'
                    f'Category: {channel.category} ({channel.category_id})\n'
                    f'Server: {channel.guild} ({channel.guild.id})\n'
                    f'Created at: {channel.created_at.strftime("%b %d, %Y (%H:%M:%S)")} '
                    f'({(datetime.datetime.utcnow() - channel.created_at).days} days ago)\n'
                )

            else:
                await ctx.send('Received unknown channel type')
                return

            await ctx.send(embed=embed)
            return

        if (guild := self.bot.get_guild(obj_id)):
            await ctx.send(
                embed=discord.Embed(
                    color=0x5050fa,
                    title=f'Server {guild}',
                    description=(
                        f'Description: {guild.description}\n'
                        f'Members: {guild.member_count}\n'
                        f'Channels: {len(guild.channels)} '
                        f'(voice: {len(guild.voice_channels)} stage: {len(guild.stage_channels)})\n'
                        f'Emojis: {len(guild.emojis)}/{guild.emoji_limit}\n'
                        f'Roles: {len(guild.roles)}\n'
                        f'Created at: {guild.created_at.strftime("%b %d, %Y (%H:%M:%S)")} '
                        f'({(datetime.datetime.utcnow() - guild.created_at).days} days ago)\n\n'
                        f'[Icon url]({guild.icon_url})'
                    )
                ).set_thumbnail(url=guild.icon_url)
            )
            return

        if (emoji := self.bot.get_emoji(obj_id)):
            await ctx.send(
                embed=discord.Embed(
                    color=0x5050fa,
                    title=f'Emoji {emoji.name}',
                    description=(
                        f'From {emoji.guild} ({emoji.guild_id})\n'
                        f'Created at: {emoji.created_at.strftime("%b %d, %Y (%H:%M:%S)")} '
                        f'({(datetime.datetime.utcnow() - emoji.created_at).days} days ago)\n\n'
                        f'[Image url]({emoji.url})'
                    )
                ).set_thumbnail(url=emoji.url)
            )
            return

        await ctx.send('No object was found')

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Pong!"""
        init_time = time.perf_counter()
        ping_msg = await ctx.send(
            embed=discord.Embed(
                color=0x50fa80,
                title='Pong!',
                description=(
                    f'Ws latency: {self.bot.latency*1000:.0f}ms\n'
                    f'Bot latency: ...'
                )
            )
        )

        await ping_msg.edit(
            embed=discord.Embed(
                color=0x50fa80,
                title='Pong!',
                description=(
                    f'Ws latency: {self.bot.latency*1000:.0f}ms\n'
                    f'Full latency: {(time.perf_counter()-init_time)*1000:.0f}ms'
                )
            )
        )

    @commands.command(hidden=True)
    async def pong(self, ctx: commands.Context):
        await ctx.send(
            embed=discord.Embed(
                color=0xfab0d0,
                title='no way！！',
                description='ʰᵒʷ'
            ).set_image(
                url='https://media.giphy.com/media/fvA1ieS8rEV8Y/giphy.gif'
            ).set_footer(
                text='how they doing that??⁇?⁈'
            )
        )


def setup(bot):
    bot.add_cog(Info(bot))
