import datetime
import re
import zoneinfo

import discord
import fuzzywuzzy.fuzz
import fuzzywuzzy.process
from discord.ext import commands


class Info(commands.Cog):
    @commands.command()
    async def time(self, ctx, *, timezone: str):
        """Gets current time in given timezone"""
        if re.fullmatch(r'(UTC|GMT)?[+-]?\d\d?:?(\d\d)?', timezone):
            if re.search(r'\d:?\d\d', timezone):
                offset = datetime.timedelta(
                    hours=int(re.findall(r'-?\d\d?(?=:?\d\d$)', timezone)[0]),
                    minutes=int(re.findall(r'-?', timezone)[0] + re.findall(r'\d\d$', timezone)[0])
                )

            else:
                offset = datetime.timedelta(hours=int(re.findall(r'\d+', timezone)[0]))

            if offset.days >= 1:
                raise commands.BadArgument('Invalid offset (>= 24 hrs)')

            dt = datetime.datetime.now(datetime.timezone(offset))
            offset_formmated = re.sub(r"(-?\d\d?):?(\d\d)$", r"\1:\2", timezone)
            if '-' not in timezone: offset_formmated = '+' + offset_formmated
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

            zone_offset = ('+' if abs(dt.utcoffset()) == dt.utcoffset() else '-') \
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


def setup(bot):
    bot.add_cog(Info())
