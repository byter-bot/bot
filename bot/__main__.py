import json
import pkgutil
import traceback
from pathlib import Path

import discord
from discord.ext import commands

from bot import exts


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
        def _imp_err(name):
            raise ImportError(name=name)

        for module in pkgutil.walk_packages(exts.__path__, exts.__name__ + '.', onerror=_imp_err):
            self.load_extension(module.name)


bot = ByterBot()
bot.run(open('TOKEN').read())
