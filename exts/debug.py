import fcntl
import os
import signal
import time
import traceback
from pathlib import Path

from discord.ext import commands


class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        exts_fd = os.open('exts', os.O_RDONLY)
        fcntl.fcntl(exts_fd, fcntl.F_SETSIG)
        fcntl.fcntl(exts_fd, fcntl.F_NOTIFY, fcntl.DN_MODIFY | fcntl.DN_CREATE)
        signal.signal(signal.SIGIO, self.handle_sig)

    def handle_sig(self, *_):
        for ext in Path('exts').glob('*.py'):
            ext_name = str(ext)[:-3].replace('/', '.')
            time.sleep(0.1)
            try:
                if ext_name in self.bot.extensions:
                    self.bot.reload_extension(ext_name)

                else:
                    self.bot.load_extension(ext_name)

            except commands.NoEntryPointError:
                pass

            except commands.ExtensionError:
                traceback.print_exc()

def setup(bot):
    if 'BYTER_DEBUG' in os.environ and os.environ['BYTER_DEBUG'] == '1' or Path('DEBUG').exists():
        bot.add_cog(Debug(bot))
