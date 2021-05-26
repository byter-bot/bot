import json
import traceback
from collections import namedtuple
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands

CFG_DEFAULTS = {
    "prefix": [],
    "reactions": {},
    "case_insensitive": True,
    "intents": {
        "guilds": True,
        "guild_messages": True,
        "guild_reactions": True
    }
}

# Create an namedtuple object with CFG_DEFAULTS and config.json, which lets us access
# values using their name as properties
CFG = namedtuple('Config', CFG_DEFAULTS)(**CFG_DEFAULTS|json.load(open('config.json')))

class ByterBot(commands.Bot):
    def __init__(self):
        super().__init__(
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False, replied_user=True
            ),
            command_prefix=commands.when_mentioned_or(*CFG.prefix),
            case_insensitive=CFG.case_insensitive,
            intents=discord.Intents(**CFG.intents)
        )

        self.session = None

        # Try to load all extensions on exts, ignore files without a
        # setup entry point func and print other errors
        for ext in Path('exts').glob('*.py'):
            try:
                self.load_extension(str(ext)[:-3].replace('/', '.'))

            except commands.NoEntryPointError:
                pass

            except commands.ExtensionError:
                traceback.print_exc()

    async def on_ready(self):
        self.session = aiohttp.ClientSession(loop=self.loop)

    async def on_disconnect(self):
        await self.session.close()


bot = ByterBot()
bot.run(open('TOKEN').read())
