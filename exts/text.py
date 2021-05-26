import base64
import hashlib
import io
import textwrap
import typing
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
    async def text2binary(self, ctx, *, text: str):
        """Encodes given text to binary ascii"""
        encoded = ' '.join(f'{ord(i):0>8b}' for i in text)
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
    async def binary2text(self, ctx, *, text: str):
        """Decodes given binary text"""
        text = [i for i in text if i in '01']
        decoded = [text[i:i+8] for i in range(0, len(text), 8)]
        decoded = ''.join(chr(int(''.join(i), base=2)) for i in decoded)
        out, trunc = codeblock_and_trunc(decoded)
        await ctx.send(
            embed=discord.Embed(
                color=0x50fa50,
                title='Decoded binary text',
                description=out
            ),
            file=trunc
        )

    @commands.command(aliases=['b64encode', 'base64', 'b64'])
    async def text2base64(self, ctx, *, text: str):
        """Encodes given text to base64"""
        encoded = base64.b64encode(text.encode()).decode()
        out, trunc = codeblock_and_trunc(encoded)
        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title='Encoded base64 text',
                description=out
            ),
            file=trunc
        )

    @commands.command(aliases=['b64decode', 'b642t', 'b64d'])
    async def base642text(self, ctx, *, text: str):
        """Decodes given base64 text"""
        try:
            decoded = base64.b64decode(text.encode(), validate=True).decode()

        except base64.binascii.Error:
            raise commands.UserInputError('invalid base64 code given')

        out, trunc = codeblock_and_trunc(decoded)
        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title='Decoded base64 text',
                description=out
            ),
            file=trunc
        )


    @commands.command(aliases=['uc'])
    async def unicodeinfo(self, ctx, char):
        """Gives info about a unicode character"""
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

    @commands.command(aliases=['hash'])
    async def hashtext(self, ctx, algo: typing.Optional[str], *, text: typing.Optional[str]):
        """Hashes given text with chosen algo

        Run this command to list available algorithms"""
        if algo is None:
            await ctx.send(
                embed=discord.Embed(
                    color=0x5050fa,
                    title=f'Available hash algorithms:',
                    description=', '.join(
                        f'`{i}`' for i in hashlib.algorithms_available
                        if not i.startswith('shake')
                    )
                )
            )
            return

        if text is None:
            raise commands.UserInputError('text is required when algo is given')

        if algo not in hashlib.algorithms_available or algo.startswith('shake'):
            raise commands.BadArgument(f'Hash {algo} does not exist or is unsupported')

        hashed = hashlib.new(algo, data=text.encode())
        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title=algo,
                description=(
                    f'hex digest → `{hashed.hexdigest()}`\n'
                    f'raw digest → `{hashed.digest()}`\n'
                    f'decoded → `{hashed.digest().decode(errors="replace")!r}`'
                )
            )
        )


def setup(bot):
    bot.add_cog(Text(bot))
