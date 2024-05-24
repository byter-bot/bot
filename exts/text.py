import hashlib
import io
import textwrap
import unicodedata

import discord
from discord.ext import commands


codeblock_wrapper = textwrap.TextWrapper(
    width=1000, placeholder='…', initial_indent='```nim\n',
    break_on_hyphens=False, replace_whitespace=False,
    drop_whitespace=False
)

def codeblock_and_trunc(text: str):
    """Utility function to return codeblock + file if it exceeds 600 chars"""
    trunc = None
    text = str(text)
    if text == '':
        return None, None

    formatted = codeblock_wrapper.fill(text)
    if len(formatted) > 600:
        trunc = discord.File(io.StringIO(textwrap.fill(text)), 'trunc.txt')
        formatted = formatted[:400] + '…'

    formatted = formatted + '\n```'
    return formatted, trunc


class Text(commands.Cog):
    """Collection of commands for text manipulation, encoding & decoding, etc"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['bin', 't2bin'])
    async def text2binary(self, ctx, *, message: str):
        """Encodes given text to binary ascii"""
        encoded = ' '.join(f'{ord(i):0>8b}' for i in message)
        out, trunc = codeblock_and_trunc(encoded)
        await ctx.send(
            embed=discord.Embed(
                color=0x50fa50,
                title='Encoded binary text',
                description=out
            ),
            file=trunc
        )

    @commands.command(aliases=['bin2t'])
    async def binary2text(self, ctx, *, message: str):
        """Decodes given binary text"""
        message = [i for i in message if i in '01']
        decoded = [message[i:i+8] for i in range(0, len(message), 8)]
        decoded = ''.join(chr(int(''.join(i), base=2)) for i in decoded)
        out, trunc = codeblock_and_trunc(decoded)
        await ctx.send(
            embed=discord.Embed(
                color=0x50fa50,
                title='decoded binary text',
                description=out
            ),
            file=trunc
        )

    @commands.command(aliases=['uc'])
    async def unicodeinfo(self, ctx, char):
        if len(char) > 1:
            try:
                char = chr(int(char.strip('uU+'), base=16))

            except ValueError:
                raise commands.BadArgument('Invalid unicode point')

        try:
            category = unicodedata.category(char)
            name = unicodedata.name(char)

        except ValueError:
            await ctx.send("I couldn't find data for that")
            return

        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title=f'Unicode info for U+{ord(char):0>4x}',
                description=f'{category} {name}\nChar: `{char}`'
            )
        )

    @commands.command(name='hash')
    async def _hash():
        pass


def setup(bot):
    bot.add_cog(Text(bot))