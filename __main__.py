import json
import traceback
from pathlib import Path

import discord
from discord.ext import commands


CFG = json.load(open('config_defaults.json')) | json.load(open('config.json'))

class ByterBot(commands.Bot):
    def __init__(self):
        super().__init__(
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False, replied_user=True
            ),
            command_prefix=commands.when_mentioned_or(*CFG['prefix']),
            case_insensitive=True,
            intents=discord.Intents(**CFG['intents'])
        )

        self.config = CFG

        # Try to load all extensions on exts, ignore files without a
        # setup entry point func and print other errors
        for ext in Path('exts').glob('*.py'):
            try:
                self.load_extension(str(ext)[:-3].replace('/', '.'))

            except commands.NoEntryPointError:
                pass

            except commands.ExtensionError:
                traceback.print_exc()


bot = ByterBot()
bot.run(open('TOKEN').read())
