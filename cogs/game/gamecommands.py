import random
from pathlib import Path
import discord
import copy
import asyncio
from discord.ext import commands
from cogs.achievements import hooks
import functools
import os
import sys
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass, field

WORD_LENGTH = 5
MAX_ATTEMPTS = 6

BASE_PATH = Path(__file__).parent
ANSWERS_FILE = BASE_PATH / "answers.txt"
GUESSES_FILE = BASE_PATH / "guesses.txt"

def load_words(path: Path) -> set[str]:
    with open(path, "r", encoding="utf-8") as f:
        return {
            w.strip().lower()
            for w in f
            if len(w.strip()) == WORD_LENGTH and w.strip().isalpha()
        }

def _embed(title: str = "rubik's cube", filename: str = "", color: int = 0x00FF00) -> discord.Embed:
    e = discord.Embed(title=title, color=color)
    if filename:
        e.set_image(url=f"attachment://{filename}")
    return e

ANSWER_WORDS = load_words(ANSWERS_FILE)
GUESS_WORDS = load_words(GUESSES_FILE)
ALL_GUESS_WORDS = ANSWER_WORDS | GUESS_WORDS

if not ANSWER_WORDS:
    raise RuntimeError("answers.txt is empty or invalid")

if not ALL_GUESS_WORDS:
    raise RuntimeError("guesses.txt is empty or invalid")

def format_result(guess: str, answer: str) -> str:
    result = [None] * WORD_LENGTH
    used = [False] * WORD_LENGTH

    for i in range(WORD_LENGTH):
        if guess[i] == answer[i]:
            result[i] = "🟩"
            used[i] = True

    for i in range(WORD_LENGTH):
        if result[i] is not None:
            continue

        found = False
        for j in range(WORD_LENGTH):
            if not used[j] and guess[i] == answer[j]:
                used[j] = True
                found = True
                break

        result[i] = "🟨" if found else "⬛"

    return f"{guess.upper()} {''.join(result)}"

class WordleSession:
    def __init__(self):
        self.answer = random.choice(tuple(ANSWER_WORDS))
        self.attempts = 0
        self.lines: list[str] = []
        self.ephemeral_message: discord.Message | None = None
        self.finished = False

class GuessModal(discord.ui.Modal, title="wordle guess"):
    guess = discord.ui.TextInput(
        label="enter a 5-letter word",
        min_length=5,
        max_length=5
    )

    def __init__(self, cog, session, ctx):
        super().__init__()
        self.cog = cog
        self.session = session
        self.ctx = ctx

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.process_guess(
            interaction,
            self.session,
            self.guess.value.lower()
        )

class WordleView(discord.ui.View):
    def __init__(self, cog, session, ctx):
        super().__init__(timeout=600)
        self.cog = cog
        self.session = session
        self.ctx = ctx

    @discord.ui.button(label="guess", style=discord.ButtonStyle.primary)
    async def guess(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                "this isn't your game lil bro",
                ephemeral=True
            )

        if self.session.finished:
            return await interaction.response.send_message(
                "this game is already over",
                ephemeral=True
            )

        await interaction.response.send_modal(
            GuessModal(self.cog, self.session, self.ctx)
        )

class Wordle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions: dict[int, WordleSession] = {}

    @commands.command(name="wordle", help="start a wordle game", usage="!wordle")
    async def wordle(self, ctx: commands.Context):
        if ctx.author.id in self.sessions:
            return await ctx.reply("you already have a wordle running")

        session = WordleSession()
        self.sessions[ctx.author.id] = session

        embed = discord.Embed(
            title="🟩 wordle",
            description="press **guess** to enter a word.",
            color=discord.Color.green()
        )

        view = WordleView(self, session, ctx)
        await ctx.send(embed=embed, view=view)

    async def process_guess(self, interaction, session, guess):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        if len(guess) != WORD_LENGTH or guess not in ALL_GUESS_WORDS:
            return await interaction.followup.send(
                "❌ invalid word",
                ephemeral=True
            )

        session.attempts += 1
        line = format_result(guess, session.answer)
        session.lines.append(line)

        content = "```\n" + "\n".join(session.lines) + "\n```"

        if session.ephemeral_message is None:
            session.ephemeral_message = await interaction.followup.send(
                content=content,
                ephemeral=True
            )
        else:
            await session.ephemeral_message.edit(content=content)

        if guess == session.answer:
            session.finished = True
            await self.finish_game(interaction, session, won=True)     
            await hooks.on_wordle(self.bot, interaction.user)

        elif session.attempts >= MAX_ATTEMPTS:
            session.finished = True
            await self.finish_game(interaction, session, won=False)

    @commands.command(name="rps", help="play roshambo with someone")
    async def rps(self, ctx: commands.Context, opponent: discord.Member):
        if opponent == ctx.author:
            return await ctx.send("you cant play with yourself you schizophrenic maniac")

        class RPSView(discord.ui.View):
            def __init__(self, author: discord.Member, opponent: discord.Member):
                super().__init__(timeout=30)
                self.author = author
                self.opponent = opponent
                self.choices: dict[int, str] = {}
                self.message: discord.Message | None = None

                if opponent.bot:
                    self.choices[opponent.id] = random.choice(["Rock", "Paper", "Scissors"])

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user.id not in (self.author.id, self.opponent.id):
                    await interaction.response.send_message(
                        "this aint your game bud", ephemeral=True
                    )
                    return False
                return True

            async def pick(self, interaction: discord.Interaction, choice: str):
                uid = interaction.user.id

                if uid in self.choices:
                    return await interaction.response.send_message(
                        "buddy you already picked", ephemeral=True
                    )

                self.choices[uid] = choice
                await interaction.response.send_message(
                    f"your pick is **{choice}**", ephemeral=True
                )

                if len(self.choices) == 2:
                    self.stop()

            @discord.ui.button(label="rock 🗿", style=discord.ButtonStyle.primary)
            async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.pick(interaction, "Rock")

            @discord.ui.button(label="paper 📄", style=discord.ButtonStyle.primary)
            async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.pick(interaction, "Paper")

            @discord.ui.button(label="scissors ✂️", style=discord.ButtonStyle.primary)
            async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.pick(interaction, "Scissors")

            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                if self.message:
                    await self.message.edit(view=self)

        view = RPSView(ctx.author, opponent)
        msg = await ctx.send(
            f"{opponent.mention}, {ctx.author.mention} has challenged you to **rock paper siciscisors**",
            view=view
        )
        view.message = msg

        await view.wait()

        for child in view.children:
            child.disabled = True
        await msg.edit(view=view)

        if len(view.choices) < 2:
            return await ctx.send("game timed out cuz yall are turtles")

        a = view.choices[ctx.author.id]
        b = view.choices[opponent.id]

        outcomes = {
            ("rock", "scissors"),
            ("scissors", "paper"),
            ("paper", "rock"),
        }

        if a == b:
            result = f"its tied. both picked **{a}**."
        elif (a, b) in outcomes:
            result = f"🏆 {ctx.author.mention} won!! **{a}** beats **{b}** fr"
        else:
            result = f"🏆 {opponent.mention} won!! **{b}** beats **{a}** fr"

        await ctx.send(result)

    async def finish_game(
        self,
        interaction: discord.Interaction,
        session: WordleSession,
        won: bool
    ):
        emoji_lines = [
            line.split(" ", 1)[1]
            for line in session.lines
        ]

        title = "🟩 wordle" if won else "⬛ wordle"

        embed = discord.Embed(
            title=title,
            description="\n".join(emoji_lines),
            color=discord.Color.green() if won else discord.Color.dark_gray()
        )

        embed.set_author(
            name=str(interaction.user),
            icon_url=interaction.user.display_avatar.url
        )

        embed.add_field(
            name="answer",
            value=f"||{session.answer.upper()}||",
            inline=False
        )

        await interaction.channel.send(
            content=interaction.user.mention,
            embed=embed
        )

        del self.sessions[interaction.user.id]

async def setup(bot: commands.Bot):
    await bot.add_cog(Wordle(bot))
