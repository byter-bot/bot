import asyncio
import fcntl
import os
import signal
import time
import traceback
from pathlib import Path

import discord
from discord.ext import commands


class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        exts_fd = os.open('exts', os.O_RDONLY)
        fcntl.fcntl(exts_fd, fcntl.F_SETSIG)
        fcntl.fcntl(exts_fd, fcntl.F_NOTIFY, fcntl.DN_MODIFY | fcntl.DN_CREATE)
        signal.signal(signal.SIGIO, self.handle_sig)

    def handle_sig(self, sig, frm):
        for ext in Path('exts').glob('*.py'):
            ext_name = str(ext)[:-3].replace('/', '.')
            if ext.stat().st_mtime - time.time() < 1:
                time.sleep(0.1)
                if ext_name in self.bot.extensions:
                    self.bot.reload_extension(ext_name)

                else:
                    try:
                        self.bot.load_extension(ext_name)

                    except commands.NoEntryPointError:
                        pass

                    except commands.ExtensionError:
                        traceback.print_exc()

def setup(bot):
    if 'BYTER_DEBUG' in os.environ and os.environ['BYTER_DEBUG'] == 1:
        print('Debug mode is on.')
        bot.add_cog(Debug(bot))