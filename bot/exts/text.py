import base64
import hashlib
import io
import re
import time
import unicodedata
from typing import Optional

import PIL
import discord
from PIL import Image
from discord.ext import commands

from bot.utils.formatting import codeblock


class Text(commands.Cog):
    """Collection of commands for text manipulation, encoding & decoding, etc"""
    @commands.command(aliases=['binary', 'bin'])
    async def binaryencode(self, ctx: commands.Context, *, text: str):
        """Encodes given text to binary ascii"""
        encoded = ' '.join(f'{ord(i):0>8b}' for i in text)
        await ctx.send(
            embed=discord.Embed(
                color=0x50fa50,
                title='Encoded binary text',
                description=codeblock(encoded, fmt='c')
            ),
            file=discord.File(io.StringIO(encoded), 'trunc.txt') if len(encoded) > 1015 else None
        )

    @commands.command(aliases=['bindec'])
    async def binarydecode(self, ctx: commands.Context, *, text: str):
        """Decodes given binary text"""
        text = [i for i in text if i in '01']
        decoded = [text[i:i+8] for i in range(0, len(text), 8)]
        decoded = ''.join(chr(int(''.join(i), base=2)) for i in decoded)
        await ctx.send(
            embed=discord.Embed(
                color=0x50fa50,
                title='Decoded binary text',
                description=codeblock(decoded, fmt=None)
            ),
            file=discord.File(io.StringIO(decoded), 'trunc.txt') if len(decoded) > 1016 else None
        )

    @commands.command(aliases=['base64', 'b64'])
    async def base64encode(self, ctx: commands.Context, *, text: str):
        """Encodes given text to base64"""
        encoded = base64.b64encode(text.encode()).decode(errors='replace')
        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title='Encoded base64 text',
                description=codeblock(encoded, fmt=None)
            ),
            file=discord.File(io.StringIO(encoded), 'trunc.txt') if len(encoded) > 1016 else None
        )

    @commands.command(aliases=['b64dec'])
    async def base64decode(self, ctx: commands.Context, *, text: str):
        """Decodes given base64 text"""
        try:
            decoded = base64.b64decode(text.encode(), validate=True).decode(errors='replace')

        except base64.binascii.Error:
            raise commands.UserInputError('invalid base64 code given')

        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title='Decoded base64 text',
                description=codeblock(decoded, fmt=None)
            ),
            file=discord.File(io.StringIO(decoded), 'trunc.txt') if len(decoded) > 1016 else None
        )

    @commands.command(aliases=['uc'])
    async def unicodeinfo(self, ctx: commands.Context, *, char: str):
        """Gives info about a unicode character

        Char can be a single character, an hex number, or the *full* character name"""
        if len(char) > 1:
            try:
                char = chr(int(char.strip('uU+'), base=16))

            except ValueError:
                try:
                    char = unicodedata.lookup(char)

                except KeyError:
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
    async def hashtext(self, ctx: commands.Context, algo: Optional[str], *, text: Optional[str]):
        """Hashes given text with chosen algo

        Run this command to list available algorithms"""
        if algo is None:
            await ctx.send(
                embed=discord.Embed(
                    color=0x5050fa,
                    title='Available hash algorithms:',
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
                    f'decoded → `{hashed.digest().decode(errors="replace")}`'
                )
            )
        )

    @commands.command(aliases=['mono'])
    async def fullwidth(self, ctx: commands.Context, *, text: str):
        """ｗｉｄｅ"""
        # Translate ascii -> fullwidth by adding 0xfee0, but use U+3000 for spaces
        translation_table = dict(zip(range(0x21, 0x7e), range(0xff01, 0xff5e)))
        translation_table.update({0x20: 0x3000})
        fullwidth_text = text.translate(translation_table)
        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title='Full-width text',
                description=fullwidth_text
            )
        )

    @commands.command(aliases=['re'])
    async def regex(self, ctx: commands.Context, pattern: str, *, text: str):
        """Match regex pattern against text"""
        init_time = time.perf_counter()
        if text is None:
            if ctx.message.reference is None:
                raise commands.BadArgument('text was omitted but there is no reply')

            text = (await ctx.fetch_message(ctx.message.reference.message_id)).content

        try:
            match = re.search(pattern.strip('`'), text)

        except re.error as exc:
            await ctx.send(
                embed=discord.Embed(
                    color=0xfa5050,
                    title='Regex error!',
                    description=str(exc)
                )
            )
            return

        if match:
            await ctx.send(
                embed=discord.Embed(
                    color=0x5050fa,
                    title='Regex match',
                    description=(
                        f'Full match ({match.end() - match.start()}): `{match.group(0)}`\n'
                        f'Groups: `{match.groups()}`'
                    )
                ).set_footer(text=f'processed in {(time.perf_counter()-init_time)*1000:.5f}ms')
            )

        else:
            await ctx.send(
                embed=discord.Embed(
                    color=0xfa7050,
                    title='No matches!'
                ).set_footer(text=f'processed in {(time.perf_counter()-init_time)*1000:.5f}ms')
            )

    @commands.command(aliases=['sre'])
    async def sregex(self, ctx: commands.Context, pattern: str, replacement: str, *, text: str):
        """Regex replacement"""
        init_time = time.perf_counter()
        if text is None:
            if ctx.message.reference is None:
                raise commands.BadArgument('text was omitted but there is no reply')

            text = (await ctx.fetch_message(ctx.message.reference.message_id)).content

        try:
            repl, num = re.subn(pattern.strip('`'), replacement.strip('`'), text)

        except re.error as exc:
            await ctx.send(
                embed=discord.Embed(
                    color=0xfa5050,
                    title='Regex error!',
                    description=str(exc)
                )
            )
            return

        await ctx.send(
            embed=discord.Embed(
                color=0x5050fa,
                title='Regex repl',
                description=(
                    f'Result: `{repl}`\n'
                    f'Replacements: {num}'
                )
            ).set_footer(text=f'processed in {(time.perf_counter()-init_time)*1000:.5f}ms')
        )

    @commands.command(aliases=['asciiart'])
    async def textimg(self, ctx: commands.Context, width: Optional[int] = 48):
        """Converts an image to text

        · Image must be an attachment and under 10 mb
        · Large images are sent through DMs"""
        if not 1 <= width <= 320:
            raise commands.BadArgument('width out of range (1 to 320)')

        if not ctx.message.attachments:
            raise commands.BadArgument('missing attachment')

        if ctx.message.attachments[0].size > 1e7:  # 10 mb
            raise commands.BadArgument('file too large')

        init_time = time.perf_counter()
        try:
            image = Image.open(io.BytesIO(await ctx.message.attachments[0].read()))
            load_time = time.perf_counter()

        except PIL.UnidentifiedImageError:
            raise commands.BadArgument('invalid image')

        if image.size[1]/(image.size[0]/width)//1.8 >= 320:
            raise commands.UserInputError('file height is too high!')

        # Make alpha bg black, resize image and convert to greyscale
        image = Image.alpha_composite(
            Image.new('RGBA', image.size, (0, 0, 0)),
            image.convert(mode='RGBA')
        )
        image = image.resize((width, int((image.size[1]/(image.size[0]/width))//1.8)))
        image = image.convert(mode='L')

        # Iter through entire image and create the resulting text with unicode block elements
        output = [
            ''.join(
                ' ░░▒▒▓▓█'[image.getpixel((x, y))//32]
                for x in range(image.size[0])
            )
            for y in range(image.size[1])
        ]

        # Trim trailing blank lines
        while output[0] == ' ' * width:
            output = output[1:]

        while output[-1] == ' ' * width:
            output = output[:-1]

        output = '\n'.join(output)
        if len(output) < 1500 and max(image.size) < 70:
            await ctx.send(
                f'```{output}```'
                f'`{image.size[0]}x{image.size[1]}`\n'
                f'loaded in {(load_time-init_time)*1000:.0f}ms\n'
                f'processed in {(time.perf_counter()-load_time)*1000:.0f}ms\n'
            )

        else:
            if len(output) < 1900 and image.size[1] < 70:
                await ctx.author.send(
                    f"Here's your image!\n"
                    f'```{output}```'
                    f'`{image.size[0]}x{image.size[1]}`\n'
                    f'loaded in {(time.perf_counter()-load_time)*1000}ms\n'
                    f'processed in {(init_time-load_time)*1000}ms'
                )

            else:
                await ctx.author.send(
                    f"Here's your image!\n"
                    f'`{image.size[0]}x{image.size[1]}`\n'
                    f'loaded in {(time.perf_counter()-load_time)*1000}ms\n'
                    f'processed in {(init_time-load_time)*1000}ms',
                    file=discord.File(io.StringIO(output), 'image.txt')
                )

            await ctx.message.add_reaction('\N{white heavy check mark}')


def setup(bot):
    bot.add_cog(Text(bot))
