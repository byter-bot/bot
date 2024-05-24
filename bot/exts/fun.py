import asyncio
import re
import secrets

import aiohttp
import discord
import numpy as np
from discord.ext import commands

# left, down, up & right arrows, plus an X
ARROW_EMOTES = ['\u2b05', '\u2b07', '\u2b06', '\u27a1', '\u274c']


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild.id == self.bot.config['main_guild_id']:
            return

        for reaction, triggers in self.bot.config['reactions'].items():
            for trigger in triggers:
                match = re.search(  # match trigger if it's a word, ignore non-word characters
                    r'(\s|^){}+(\s|$)'.format(trigger),
                    re.sub(r'[^\w\s]', '', message.content),
                    flags=re.IGNORECASE
                )

                if match:
                    if reaction.isdecimal():
                        reaction = self.bot.get_emoji(int(reaction))

                    await message.add_reaction(reaction)
                    break

    @commands.command()
    async def cat(self, ctx: commands.Context):
        """cat"""
        async with aiohttp.ClientSession(loop=self.bot.loop) as session:
            resp = await session.get("https://api.thecatapi.com/v1/images/search")
            if resp.ok:
                json = await resp.json()
                url = json[0]['url']
                await ctx.send(embed=discord.Embed(color=0x5050fa, title='Cat!!').set_image(url=url))

            else:
                await ctx.send("Couldn't get a cat image <:creustickersad:726924232461910077>")

    @commands.command(name='2048')
    @commands.cooldown(1, 30)
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True)
    async def _2048(self, ctx: commands.Context, size: int = 4):
        if not 2 <= size <= 8:
            raise commands.BadArgument('size must be between 2 and 8')

        tiles = self.bot.config['minigame_emoji']['2048']

        def comp(line):
            """Move cells left. 0 2 0 2 -> 2 2 0 0"""
            for index, cell, n_cell in zip(range(len(line)), line[:-1], line[1:]):
                if cell == 0 and n_cell > 0:  # Swap cells if valid and skip to next iteration
                    line[index:index + 2] = (n_cell, 0)
                    break
            else:
                return line
            return comp(line)

        def merge_line(line, score):
            """Merge and move cells left, merging only happens once per cell"""
            line = comp(line)
            for index, cell, n_cell in zip(range(len(line)), line[:-1], line[1:]):
                if cell != 0 and cell == n_cell:
                    line[index:index + 2] = (cell + 1, 0)
                    score += 2**(cell + 1)
            return comp(line), score

        def merge_lines(board, direction, score):
            """Merge all lines within a board in given direction"""
            merged = np.rot90(board.copy(), k=direction)
            for index, line in enumerate(merged):
                merged[index], score = merge_line(line, score)

            return np.rot90(merged, k=direction * -1), score

        def can_merge(board, direction):
            """Check if any movement is posible"""
            return not np.array_equal(board, merge_lines(board, direction, 0)[0])

        game = await ctx.send(embed=discord.Embed(color=0xfafafa, title='Just a bit...'))
        board = np.zeros((size, size), int)
        score = 0
        move_count = 0
        game_won = False
        while any(can_merge(board, direction) for direction in range(4)) or not board.any():
            for emote in ARROW_EMOTES:
                await game.add_reaction(emote)

            # Find non-zero positions, pick one and set it to either 1 or 2
            valid_positions = []
            for x, line in enumerate(board):
                for y, cell in enumerate(line):
                    if cell == 0:
                        valid_positions.append((x, y))

            if valid_positions:
                board[secrets.choice(valid_positions)] = 1 if secrets.randbelow(11) < 10 else 2

            if not game_won and 11 in board:  # 2^11 -> 2048
                await ctx.send('You reached 2048! Congratulations!!')
                game_won = True

            await game.edit(
                embed=discord.Embed(
                    color=0x5050fa,
                    title='2048!',
                    description='\n'.join(''.join(tiles[j] for j in i) for i in board)
                ).add_field(name='\u200c', value=f'**Score:** {score}\n**Moves:** {move_count}')
            )

            try:
                while True:  # Loop checking for reactions until one is a valid move
                    reaction, _ = await self.bot.wait_for(
                        'reaction_add',
                        timeout=120,
                        check=lambda r, u: u == ctx.author and r.message == game and str(r) in ARROW_EMOTES
                    )

                    await reaction.remove(ctx.author)

                    if str(reaction.emoji) == '\u274c':  # An X
                        await game.edit(
                            embed=discord.Embed(
                                color=0xfafa60,
                                title='Game ended!',
                                description='\n'.join(''.join(tiles[j] for j in i) for i in board)
                            ).add_field(name='\u200c', value=f'**Score:** {score}\n**Moves:** {move_count}')
                        )
                        return

                    if can_merge(board, [0, 3, 1, 2][ARROW_EMOTES.index(str(reaction.emoji))]):
                        break

            except asyncio.TimeoutError:
                await game.edit(
                    embed=discord.Embed(
                        color=0xfafa60,
                        title='Timed out, game ended!',
                        description='\n'.join(''.join(tiles[j] for j in i) for i in board)
                    ).add_field(name='\u200c', value=f'**Score:** {score}\n**Moves:** {move_count}')
                )
                return

            direction = [0, 3, 1, 2][ARROW_EMOTES.index(str(reaction.emoji))]
            board, score = merge_lines(board, direction, score)
            move_count += 1

        await game.edit(
            embed=discord.Embed(
                color=0xfafa60,
                title='No moves, game ended!',
                description='\n'.join(''.join(tiles[j] for j in i) for i in board)
            ).add_field(name='\u200c', value=f'**Score:** {score}\n**Moves:** {move_count}')
        )


def setup(bot):
    bot.add_cog(Fun(bot))
