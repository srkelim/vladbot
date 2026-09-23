import aiohttp
import typing
import discord
from discord.ext import commands, tasks
import random
import traceback
import time
import os
import asyncio
import yt_dlp
import platform
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor
)
import math
from datetime import datetime as dt, time as dt_time, timedelta, timezone
from utils.quote_image import render_quote
from io import BytesIO
from dotenv import load_dotenv
from urllib.parse import quote_plus
from collections import defaultdict

from config import RESP_ANSWERS, RESP_WHO, RESP_WHAT, RESP_WHEN, RESP_SHOULD, RESP_WHY
from db import db
from cogs.achievements import hooks
from config import PARTHENON_CHANNEL, PARTHENON_ROLE, SIGWATER_CHANNEL, HEAVEN_CHANNEL, ICY_PEAKS_CHANNEL, ICY_PEAKS_ROLE, DREAMSKY_CHANNEL, DREAMSKY_ROLE, MINNEAPOLIS_CHANNEL, HOUSEOFVLADS_CHANNEL

load_dotenv()
API_KEY = "f6edd2a54d5682cd662c5b3878bb1a43"
AIRole = int(os.getenv("AIRole"))
DECIMAL_CAP = 10
PUZZLE_COUNT = 20
REQUIRED_SOLVES = 16
DEALER_PUZZLE_COUNT = 25
DEALER_REQUIRED_SOLVES = 18
TIME_LIMIT = 10
DEALER_TIME_LIMIT = 15
ACTIVE_TAX_FIGHTS = set()

transformations = (
    standard_transformations +
    (implicit_multiplication_application, convert_xor)
)

SAFE_GLOBALS = {
    **sp.__dict__,
    "pi": sp.pi,
    "e": sp.E,
    "i": sp.I
}

SCRAMBLE_WORDS = [
"vladbot",
"economy",
"robbery",
"minneapolis",
"vacation",
"achievement",
"discord",
"database",
"currency",
"marriage",
"adoption",
"cooldown",
"treasure",
"criminal",
"puzzle",
"reaction",
"pattern",
"python",
"channel",
"server",
"command",
"botfight",
"vacationspot",
"minigame",
"cooldowns",
"leaderboard"
]

MATH_QUESTIONS = [
("8 * 7 + 15", 71),
("24 // 3 + 6 * 5", 38),
("9 * 9 + 12 * 3", 117),
("15**2 - 200", 25),
("14 * 4 - 19", 37),
("18 * 3 + 42", 96),
("45 - 12 * 2", 21),
("60 // 3 + 17", 37),
("7 * 11 + 9", 86),
("90 // 5 + 14", 32),
("16 * 3 - 7", 41),
("22 + 8 * 6", 70),
("100 // 4 + 36", 61),
("12 * 8 + 5", 101),
("17 * 3 + 18", 69)
]

MEMORY_SEQUENCES = [
"🟥🟦🟩🟨",
"🟨🟥🟦🟩",
"🟦🟦🟥🟩",
"🟩🟨🟩🟥",
"🟥🟩🟨🟦",
"🟦🟥🟨🟩",
"🟨🟨🟥🟦",
"🟩🟥🟦🟨",
"🟦🟩🟨🟥",
"🟥🟥🟦🟩",
"🟨🟦🟥🟩",
"🟩🟩🟨🟥"
]

PATTERN_QUESTIONS = [
("2 4 8 16 ?", "32"),
("3 6 9 12 ?", "15"),
("5 10 20 40 ?", "80"),
("1 4 9 16 ?", "25"),
("7 14 21 28 ?", "35"),
("10 20 40 80 ?", "160"),
("6 12 24 48 ?", "96"),
("9 18 27 36 ?", "45"),
("11 22 44 88 ?", "176"),
("4 6 8 10 ?", "12")
]

RIDDLES = [
("i have keys but no locks", "keyboard"),
("what runs but never walks", "river"),
("what gets wetter the more it dries", "towel"),
("what has hands but cannot clap", "clock"),
("what has an eye but cannot see", "needle"),
("what goes up but never comes down", "age"),
("what has a face and two hands but no arms", "clock"),
("what has a neck but no head", "bottle"),
("what gets sharper the more you use it", "brain"),
("what has many teeth but cannot bite", "comb")
]

WORD_ELIMINATION = [
(["apple","banana","carrot","orange"], "carrot"),
(["dog","cat","lion","car"], "car"),
(["python","java","banana","c++"], "banana"),
(["discord","telegram","whatsapp","table"], "table"),
(["red","blue","green","banana"], "banana"),
(["gold","silver","bronze","pizza"], "pizza"),
(["keyboard","mouse","monitor","sandwich"], "sandwich")
]

REVERSE_WORDS = [
("TOBDALV", "vladbot"),
("YMONOCE", "economy"),
("NOITACAV", "vacation"),
("EGAIRRAM", "marriage"),
("NOITPODA", "adoption"),
("LENNAHC", "channel"),
("REVRES", "server"),
("DNAMMOC", "command"),
("NOITCAER", "reaction"),
("ODNUH ON", "no hundo"),
("31", "13")
]

DEALER_SUITS = ["♠️", "♥️", "♦️", "♣️"]
DEALER_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
DEALER_RANK_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11
}

def dealer_card():
    return random.choice(DEALER_RANKS), random.choice(DEALER_SUITS)

def card_str(card):
    return f"{card[0]}{card[1]}"

def hand_value(hand):
    total = sum(DEALER_RANK_VALUES[c[0]] for c in hand)
    aces = sum(1 for c in hand if c[0] == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def _basic_strategy_hit(player_total: int, dealer_up: int, soft: bool) -> bool:
    if soft:
        if player_total <= 17:
            return True
        if player_total == 18:
            return dealer_up in (9, 10, 11)
        return False
    else:
        if player_total <= 11:
            return True
        if player_total == 12:
            return dealer_up in (2, 3, 7, 8, 9, 10, 11)
        if player_total <= 16:
            return dealer_up >= 7
        return False

async def setup_parthenon_message(bot, channel):
    async for msg in channel.history(limit=100):
        if msg.author == bot.user:
            for row in msg.components:
                for comp in row.children:
                    if getattr(comp, "custom_id", None) == "enter_parthenon":
                        return False

    msg = await channel.send(
        embed=discord.Embed(
            title="THE GOLDEN GATE",
            description="press below to enter the parthenon.",
            color=discord.Color.gold()
        ),
        view=ParthenonView(bot)
    )

    await msg.pin(reason="Parthenon gate message")
    return True

class ParthenonView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="enter parthenon",
        style=discord.ButtonStyle.success,
        custom_id="enter_parthenon"
    )
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.user
        guild = interaction.guild

        async with db.pool.acquire() as conn:
            has_key = await conn.fetchval(
                "SELECT golden_gate_key FROM user_unlocks WHERE user_id=$1",
                member.id
            )

        if not has_key:
            return await interaction.response.send_message(
                "🗝️ you need the **golden gate key**. go to **treachery** to buy it.",
                ephemeral=True
            )

        role = guild.get_role(PARTHENON_ROLE)
        if role:
            await member.add_roles(role)

        await interaction.response.send_message(
            "🏛️ the parthenon accepts you.",
            ephemeral=True
        )

class HouseGameView(discord.ui.View):
    ROUNDS_TOTAL  = 15
    ROUNDS_NEEDED = 11

    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    @discord.ui.button(label="sit down", style=discord.ButtonStyle.danger, emoji="🃏")
    async def sit_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        channel = interaction.channel

        async with db.pool.acquire() as conn:
            already_won = await conn.fetchval(
                "SELECT house_edge FROM user_unlocks WHERE user_id=$1", member.id
            )

        if already_won:
            return await interaction.response.send_message(
                "🃏 you've already beaten the dealer. the house edge is yours.",
                ephemeral=True
            )

        self.stop()
        await interaction.response.send_message(
            embed=discord.Embed(
                description=(
                    "🃏 *the dealer cuts the deck.*\n"
                    f"*win {self.ROUNDS_NEEDED}/{self.ROUNDS_TOTAL} rounds to claim the house edge.*"
                ),
                color=discord.Color.dark_gold()
            ),
            ephemeral=True
        )

        def make_deck():
            suits = ["♠", "♥", "♦", "♣"]
            ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
            deck = [(r, s) for s in suits for r in ranks]
            random.shuffle(deck)
            return deck

        def card_val(card):
            r = card[0]
            if r in ("J","Q","K"): return 10
            if r == "A": return 11
            return int(r)

        def hand_total(hand):
            total = sum(card_val(c) for c in hand)
            aces = sum(1 for c in hand if c[0] == "A")
            while total > 21 and aces:
                total -= 10
                aces -= 1
            return total

        def hand_str(hand):
            return " ".join(f"{r}{s}" for r, s in hand)

        def is_soft(hand):
            return sum(card_val(c) for c in hand) != hand_total(hand)

        def is_red(card):
            return card[1] in ("♥", "♦")

        def check(m):
            return m.author.id == member.id and m.channel == channel

        def scoreline(w, l, rnd):
            remaining = self.ROUNDS_TOTAL - rnd
            return f"wins: **{w}** | losses: **{l}** | remaining: **{remaining}**"

        wins = 0
        losses = 0

        async def do_basic_strategy(rnd, blind=False):
            nonlocal wins, losses
            deck = make_deck()
            player = [deck.pop(), deck.pop()]
            dealer_up = deck.pop()
            ptotal = hand_total(player)
            soft = is_soft(player)
            correct = "hit" if _basic_strategy_hit(ptotal, card_val(dealer_up), soft) else "stand"
            soft_tag = " *(soft)*" if soft else ""

            if blind:
                desc = (
                    f"**your total:** `{ptotal}`{soft_tag}\n"
                    f"**dealer shows:** {dealer_up[0]}{dealer_up[1]}\n\n"
                    f"type `hit` or `stand`  *4 seconds*\n"
                    f"*bust on a hit = round lost*"
                )
            else:
                desc = (
                    f"**your hand:** {hand_str(player)} → `{ptotal}`{soft_tag}\n"
                    f"**dealer shows:** {dealer_up[0]}{dealer_up[1]}\n\n"
                    f"type `hit` or `stand`  *4 seconds*"
                )

            await channel.send(embed=discord.Embed(
                title=f"🃏 round {rnd}/{self.ROUNDS_TOTAL}",
                description=desc + f"\n\n{scoreline(wins, losses, rnd)}",
                color=discord.Color.dark_gold()
            ))

            try:
                msg = await self.bot.wait_for("message", timeout=4, check=check)
                choice = msg.content.lower().strip()
            except asyncio.TimeoutError:
                choice = ""

            if blind and choice == "hit":
                drawn = deck.pop()
                new_total = hand_total(player + [drawn])
                await channel.send(embed=discord.Embed(
                    description=f"you drew `{drawn[0]}{drawn[1]}` → total `{new_total}`",
                    color=discord.Color.blurple()
                ))
                if new_total > 21:
                    losses += 1
                    await channel.send(embed=discord.Embed(description=f"💥 bust at `{new_total}`. round lost.", color=discord.Color.red()))
                    return
                if correct == "hit":
                    wins += 1
                    await channel.send(embed=discord.Embed(description="✅ correct!! hit was right.", color=discord.Color.green()))
                else:
                    losses += 1
                    await channel.send(embed=discord.Embed(description="❌ you hit when you should have stood.", color=discord.Color.red()))
                return

            if choice == correct:
                wins += 1
                await channel.send(embed=discord.Embed(description=f"✅ correct!! **{correct}**.", color=discord.Color.green()))
            else:
                losses += 1
                await channel.send(embed=discord.Embed(description=f"❌ wrong!! correct was **{correct}**.", color=discord.Color.red()))

        async def do_red_or_black(rnd):
            nonlocal wins, losses
            await channel.send(embed=discord.Embed(
                title=f"🃏 round {rnd}/{self.ROUNDS_TOTAL}",
                description=(
                    f"the dealer is about to flip a card.\n\n"
                    f"type `red` or `black`  *6 seconds*\n\n"
                    f"{scoreline(wins, losses, rnd)}"
                ),
                color=discord.Color.dark_gold()
            ))

            try:
                msg = await self.bot.wait_for("message", timeout=6, check=check)
                choice = msg.content.lower().strip()
            except asyncio.TimeoutError:
                choice = ""

            if choice not in ("red", "black"):
                losses += 1
                await channel.send(embed=discord.Embed(description="❌ no valid answer. round lost.", color=discord.Color.red()))
                return

            deck = make_deck()
            flipped = deck.pop()
            red = is_red(flipped)
            actual = "red" if red else "black"
            emoji = "🔴" if red else "⚫"

            await channel.send(embed=discord.Embed(
                description=f"the dealer flips: {emoji} **{flipped[0]}{flipped[1]}** - **{actual}**",
                color=discord.Color.dark_gold()
            ))

            if choice == actual:
                wins += 1
                await channel.send(embed=discord.Embed(description=f"✅ correct!! **{actual}**.", color=discord.Color.green()))
            else:
                losses += 1
                await channel.send(embed=discord.Embed(description=f"❌ wrong!! it was **{actual}**.", color=discord.Color.red()))

        async def do_high_or_low(rnd):
            nonlocal wins, losses
            await channel.send(embed=discord.Embed(
                title=f"🃏 round {rnd}/{self.ROUNDS_TOTAL}",
                description=(
                    f"the dealer cuts the deck.\n\n"
                    f"type `high` *(above 7)* or `low` *(below 7)*  *8 seconds*\n"
                    f"*7 exactly = push, replays once. second push = round lost*\n\n"
                    f"{scoreline(wins, losses, rnd)}"
                ),
                color=discord.Color.dark_gold()
            ))

            for attempt in range(2):
                try:
                    msg = await self.bot.wait_for("message", timeout=8, check=check)
                    choice = msg.content.lower().strip()
                except asyncio.TimeoutError:
                    choice = ""

                if choice not in ("high", "low"):
                    losses += 1
                    await channel.send(embed=discord.Embed(description="❌ invalid choice. round lost.", color=discord.Color.red()))
                    return

                deck = make_deck()
                cut = deck.pop()
                val = card_val(cut)
                actual = "high" if val > 7 else "low" if val < 7 else "push"

                await channel.send(embed=discord.Embed(
                    description=f"cut reveals: **{cut[0]}{cut[1]}** (`{val}`)",
                    color=discord.Color.blurple()
                ))

                if actual == "push":
                    if attempt == 0:
                        await channel.send(embed=discord.Embed(description="🤝 **7! push.** round replays.", color=discord.Color.orange()))
                        await asyncio.sleep(0.6)
                        await channel.send(embed=discord.Embed(
                            description=f"type `high` or `low` again  *8 seconds*",
                            color=discord.Color.dark_gold()
                        ))
                        continue
                    else:
                        losses += 1
                        await channel.send(embed=discord.Embed(description="🤝 pushed twice. round lost.", color=discord.Color.red()))
                        return
                elif choice == actual:
                    wins += 1
                    await channel.send(embed=discord.Embed(description=f"✅ correct!! **{actual}**.", color=discord.Color.green()))
                    return
                else:
                    losses += 1
                    await channel.send(embed=discord.Embed(description=f"❌ wrong!! it was **{actual}**.", color=discord.Color.red()))
                    return

        async def do_bust_call(rnd):
            nonlocal wins, losses
            await channel.send(embed=discord.Embed(
                title=f"🃏 round {rnd}/{self.ROUNDS_TOTAL}",
                description=(
                    f"the dealer draws 3 cards blind.\n\n"
                    f"type `bust` or `safe`  *8 seconds*\n\n"
                    f"{scoreline(wins, losses, rnd)}"
                ),
                color=discord.Color.dark_gold()
            ))

            try:
                msg = await self.bot.wait_for("message", timeout=8, check=check)
                choice = msg.content.lower().strip()
            except asyncio.TimeoutError:
                choice = ""

            if choice not in ("bust", "safe"):
                losses += 1
                await channel.send(embed=discord.Embed(description="❌ invalid choice. round lost.", color=discord.Color.red()))
                return

            deck = make_deck()
            dealer_cards = [deck.pop() for _ in range(3)]
            dealer_total = hand_total(dealer_cards)
            busted = dealer_total > 21
            correct = "bust" if busted else "safe"
            cards_str = "  ".join(f"{c[0]}{c[1]}" for c in dealer_cards)

            await channel.send(embed=discord.Embed(
                description=f"dealer's cards: **{cards_str}** → `{dealer_total}`",
                color=discord.Color.blurple()
            ))

            if choice == correct:
                wins += 1
                await channel.send(embed=discord.Embed(description=f"✅ **{correct}**!! correct call.", color=discord.Color.green()))
            else:
                losses += 1
                await channel.send(embed=discord.Embed(description=f"❌ wrong!! it was **{correct}**.", color=discord.Color.red()))

        async def do_pair_spotter(rnd):
            nonlocal wins, losses
            deck = make_deck()
            dealt = [deck.pop() for _ in range(6)]
            ranks_seen = [c[0] for c in dealt]
            has_pair = len(ranks_seen) != len(set(ranks_seen))
            correct = "yes" if has_pair else "no"

            embed = discord.Embed(
                title=f"🃏 round {rnd}/{self.ROUNDS_TOTAL}",
                description="watch the cards...",
                color=discord.Color.dark_gold()
            )
            msg = await channel.send(embed=embed)

            for i, card in enumerate(dealt, 1):
                embed.description = f"**{i}/6** → {card[0]}{card[1]}"
                await msg.edit(embed=embed)
                await asyncio.sleep(0.9)

            embed.description = (
                f"was there a **pair** in those 6 cards?\n"
                f"type `yes` or `no`  *5 seconds*\n\n"
                f"{scoreline(wins, losses, rnd)}"
            )
            await msg.edit(embed=embed)

            try:
                reply = await self.bot.wait_for("message", timeout=5, check=check)
                choice = reply.content.lower().strip()
            except asyncio.TimeoutError:
                choice = ""

            shown_str = "  ".join(f"{c[0]}{c[1]}" for c in dealt)
            if choice == correct:
                wins += 1
                await channel.send(embed=discord.Embed(
                    description=f"✅ correct!! `{shown_str}` {'had a pair' if has_pair else 'had no pair'}.",
                    color=discord.Color.green()
                ))
            else:
                losses += 1
                await channel.send(embed=discord.Embed(
                    description=f"❌ wrong!! `{shown_str}` {'had a pair' if has_pair else 'had no pair'}.",
                    color=discord.Color.red()
                ))

        async def do_final_hand(rnd):
            nonlocal wins, losses
            deck = make_deck()
            player = [deck.pop(), deck.pop()]
            dealer_hand = [deck.pop(), deck.pop()]
            ptotal = hand_total(player)
            soft = is_soft(player)
            soft_tag = " *(soft)*" if soft else ""

            await channel.send(embed=discord.Embed(
                title=f"🃏 round {rnd}/{self.ROUNDS_TOTAL}",
                description=(
                    f"**your hand:** {hand_str(player)} → `{ptotal}`{soft_tag}\n"
                    f"**dealer shows:** {dealer_hand[0][0]}{dealer_hand[0][1]} + 🂠\n\n"
                    f"type `hit` *(one card)*, `stand`, or `surrender` *(forfeit round)*  *8 seconds*\n\n"
                    f"{scoreline(wins, losses, rnd)}"
                ),
                color=discord.Color.gold()
            ))

            try:
                msg = await self.bot.wait_for("message", timeout=8, check=check)
                choice = msg.content.lower().strip()
            except asyncio.TimeoutError:
                choice = "stand"

            if choice == "surrender":
                losses += 1
                await channel.send(embed=discord.Embed(description="🏳️ surrendered. round lost.", color=discord.Color.red()))
                return

            if choice == "hit":
                drawn = deck.pop()
                player.append(drawn)
                ptotal = hand_total(player)
                await channel.send(embed=discord.Embed(
                    description=f"you drew `{drawn[0]}{drawn[1]}` → total `{ptotal}`",
                    color=discord.Color.blurple()
                ))
                if ptotal > 21:
                    losses += 1
                    await channel.send(embed=discord.Embed(description=f"💥 bust at `{ptotal}`. round lost.", color=discord.Color.red()))
                    return

            while hand_total(dealer_hand) < 17:
                dealer_hand.append(deck.pop())

            dtotal = hand_total(dealer_hand)
            await channel.send(embed=discord.Embed(
                description=f"**dealer reveals:** {hand_str(dealer_hand)} → `{dtotal}`",
                color=discord.Color.blurple()
            ))

            if dtotal > 21 or ptotal > dtotal:
                wins += 1
                await channel.send(embed=discord.Embed(description=f"✅ you win!! `{ptotal}` beats `{dtotal}`.", color=discord.Color.green()))
            elif ptotal == dtotal:
                losses += 1
                await channel.send(embed=discord.Embed(description=f"🤝 push at `{ptotal}`. house takes ties. round lost.", color=discord.Color.red()))
            else:
                losses += 1
                await channel.send(embed=discord.Embed(description=f"❌ dealer wins. `{dtotal}` beats `{ptotal}`. round lost.", color=discord.Color.red()))

        schedule = [
            ("S", 1),
            ("R", 2),
            ("S", 3),
            ("H", 4),
            ("B", 5),
            ("R", 6),
            ("P", 7),
            ("C", 8),
            ("S", 9),
            ("R", 10),
            ("B", 11),
            ("H", 12),
            ("S", 13),
            ("R", 14),
            ("F", 15),
        ]

        for kind, rnd in schedule:
            remaining = self.ROUNDS_TOTAL - rnd + 1
            if wins + remaining < self.ROUNDS_NEEDED:
                await channel.send(embed=discord.Embed(
                    title="🃏 THE HOUSE WINS",
                    description=(
                        f"**{member.mention}** can no longer reach {self.ROUNDS_NEEDED} wins.\n"
                        f"final score: `{wins}/{self.ROUNDS_TOTAL}`"
                    ),
                    color=discord.Color.dark_red()
                ))
                return

            await asyncio.sleep(0.6)

            if kind == "S":
                await do_basic_strategy(rnd, blind=False)
            elif kind == "B":
                await do_basic_strategy(rnd, blind=True)
            elif kind == "R":
                await do_red_or_black(rnd)
            elif kind == "H":
                await do_high_or_low(rnd)
            elif kind == "P":
                await do_pair_spotter(rnd)
            elif kind == "C":
                await do_bust_call(rnd)
            elif kind == "F":
                await do_final_hand(rnd)

            await asyncio.sleep(0.6)

        if wins >= self.ROUNDS_NEEDED:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_unlocks (user_id, house_edge)
                    VALUES ($1, TRUE)
                    ON CONFLICT (user_id) DO UPDATE SET house_edge = TRUE
                    """,
                    member.id
                )

            await hooks.on_dealer_defeat(self.bot, member)

            await channel.send(embed=discord.Embed(
                title="🏆 YOU BEAT THE DEALER",
                description=(
                    f"**{member.mention}** won `{wins}/{self.ROUNDS_TOTAL}` rounds.\n\n"
                    f"the dealer nods.\n"
                    f"🃏 **house edge unlocked!!** your coinflip and roulette odds are permanently improved."
                ),
                color=discord.Color.gold()
            ))
        else:
            await channel.send(embed=discord.Embed(
                title="🃏 THE HOUSE WINS",
                description=(
                    f"**{member.mention}** fell short. `{wins}/{self.ROUNDS_TOTAL}` wins.\n"
                    f"needed `{self.ROUNDS_NEEDED}`."
                ),
                color=discord.Color.dark_red()
            ))

async def run_vladurk_escape(bot, channel, member) -> bool:
    solves = 0
    def check(m):
        return m.author.id == member.id and m.channel == channel

    for _ in range(PUZZLE_COUNT):
        puzzle_type = random.choice([
            "scramble", "math", "pattern", "riddle", "reverse", "memory", "elimination"
        ])

        if puzzle_type == "scramble":
            word = random.choice(SCRAMBLE_WORDS)
            scrambled = "".join(random.sample(word, len(word)))
            await channel.send(embed=discord.Embed(
                description=f"🧩 **unscramble:** `{scrambled}`", color=discord.Color.blue()
            ))
            answer = word
        elif puzzle_type == "math":
            q, a = random.choice(MATH_QUESTIONS)
            await channel.send(embed=discord.Embed(
                description=f"🧠 **solve:** `{q}`", color=discord.Color.blue()
            ))
            answer = str(a)
        elif puzzle_type == "pattern":
            q, a = random.choice(PATTERN_QUESTIONS)
            await channel.send(embed=discord.Embed(
                description=f"🔢 **complete the pattern:** `{q}`", color=discord.Color.blue()
            ))
            answer = a
        elif puzzle_type == "riddle":
            q, a = random.choice(RIDDLES)
            await channel.send(embed=discord.Embed(
                description=f"❓ **riddle:** {q}", color=discord.Color.blue()
            ))
            answer = a
        elif puzzle_type == "reverse":
            q, a = random.choice(REVERSE_WORDS)
            await channel.send(embed=discord.Embed(
                description=f"🔁 **reverse:** `{q}`", color=discord.Color.blue()
            ))
            answer = a
        elif puzzle_type == "memory":
            seq = random.choice(MEMORY_SEQUENCES)
            emoji_to_word = {"🟥": "red", "🟦": "blue", "🟩": "green", "🟨": "yellow"}
            embed = discord.Embed(description="🧠 **memorize...**", color=discord.Color.blue())
            msg = await channel.send(embed=embed)
            for i, emoji in enumerate(seq, start=1):
                embed.description = f"🧠 **{i}** - {emoji}"
                await msg.edit(embed=embed)
                await asyncio.sleep(1)
            await asyncio.sleep(1)
            embed.description = "🧠 **type the colors in order!** e.g. `red blue green yellow`"
            await msg.edit(embed=embed)
            answer = " ".join(emoji_to_word[e] for e in seq)
        elif puzzle_type == "elimination":
            options, correct = random.choice(WORD_ELIMINATION)
            await channel.send(embed=discord.Embed(
                description=f"❌ **which doesn't belong?** {', '.join(options)}", color=discord.Color.blue()
            ))
            answer = correct

        try:
            msg = await bot.wait_for("message", timeout=TIME_LIMIT, check=check)
            if msg.content.lower() == answer.lower():
                solves += 1
                await channel.send(embed=discord.Embed(description="✅ correct!", color=discord.Color.green()))
            else:
                await channel.send(embed=discord.Embed(
                    description=f"❌ wrong! answer was **{answer}**", color=discord.Color.red()
                ))
        except asyncio.TimeoutError:
            await channel.send(embed=discord.Embed(
                description=f"⏰ time's up! answer was **{answer}**", color=discord.Color.red()
            ))

    return solves >= REQUIRED_SOLVES

async def run_sigshark_escape(bot, channel, member) -> bool:
    from cogs.fishing.fishingcommands import phase_dodge, phase_reel, phase_strike
    return (
        await phase_dodge(bot, channel, member) and
        await phase_reel(bot, channel, member) and
        await phase_strike(bot, channel, member)
    )


async def run_dealer_escape(bot, channel, member) -> bool:
    ROUNDS_TOTAL  = 15
    ROUNDS_NEEDED = 11

    wins   = 0
    losses = 0

    def make_deck():
        suits = ["♠", "♥", "♦", "♣"]
        ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
        deck = [(r, s) for s in suits for r in ranks]
        random.shuffle(deck)
        return deck

    def card_val(card):
        r = card[0]
        if r in ("J","Q","K"): return 10
        if r == "A": return 11
        return int(r)

    def hand_total(hand):
        total = sum(card_val(c) for c in hand)
        aces = sum(1 for c in hand if c[0] == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def hand_str(hand):
        return " ".join(f"{r}{s}" for r, s in hand)

    def is_soft(hand):
        return sum(card_val(c) for c in hand) != hand_total(hand)

    def is_red(card):
        return card[1] in ("♥", "♦")

    def check(m):
        return m.author.id == member.id and m.channel == channel

    def scoreline(w, l, rnd):
        return f"wins: **{w}** | losses: **{l}** | remaining: **{ROUNDS_TOTAL - rnd}**"

    async def do_basic_strategy(rnd, blind=False):
        nonlocal wins, losses
        deck = make_deck()
        player = [deck.pop(), deck.pop()]
        dealer_up = deck.pop()
        ptotal = hand_total(player)
        soft = is_soft(player)
        correct = "hit" if _basic_strategy_hit(ptotal, card_val(dealer_up), soft) else "stand"
        soft_tag = " *(soft)*" if soft else ""
        desc = (
            f"**your total:** `{ptotal}`{soft_tag}\n**dealer shows:** {dealer_up[0]}{dealer_up[1]}\n\n"
            f"type `hit` or `stand` *4 seconds*\n*bust on a hit = round lost*"
        ) if blind else (
            f"**your hand:** {hand_str(player)} → `{ptotal}`{soft_tag}\n"
            f"**dealer shows:** {dealer_up[0]}{dealer_up[1]}\n\ntype `hit` or `stand` *4 seconds*"
        )
        await channel.send(embed=discord.Embed(
            title=f"🃏 round {rnd}/{ROUNDS_TOTAL}\n{scoreline(wins,losses,rnd)}",
            description=desc, color=discord.Color.dark_gold()
        ))
        try:
            msg = await bot.wait_for("message", timeout=4, check=check)
            choice = msg.content.lower().strip()
        except asyncio.TimeoutError:
            choice = ""
        if blind and choice == "hit":
            drawn = deck.pop()
            new_total = hand_total(player + [drawn])
            await channel.send(embed=discord.Embed(description=f"drew `{drawn[0]}{drawn[1]}` → `{new_total}`", color=discord.Color.blurple()))
            if new_total > 21:
                losses += 1
                await channel.send(embed=discord.Embed(description=f"💥 bust. round lost.", color=discord.Color.red()))
                return
            if correct == "hit":
                wins += 1
                await channel.send(embed=discord.Embed(description="✅ correct.", color=discord.Color.green()))
            else:
                losses += 1
                await channel.send(embed=discord.Embed(description="❌ should have stood.", color=discord.Color.red()))
            return
        if choice == correct:
            wins += 1
            await channel.send(embed=discord.Embed(description=f"✅ correct!! **{correct}**.", color=discord.Color.green()))
        else:
            losses += 1
            await channel.send(embed=discord.Embed(description=f"❌ wrong!! correct was **{correct}**.", color=discord.Color.red()))

    async def do_red_or_black(rnd):
        nonlocal wins, losses
        await channel.send(embed=discord.Embed(
            title=f"🃏 round {rnd}/{ROUNDS_TOTAL}\n{scoreline(wins,losses,rnd)}",
            description="the dealer flips a card.\ntype `red` or `black` *6 seconds*", color=discord.Color.dark_gold()
        ))
        try:
            msg = await bot.wait_for("message", timeout=6, check=check)
            choice = msg.content.lower().strip()
        except asyncio.TimeoutError:
            choice = ""
        if choice not in ("red", "black"):
            losses += 1
            await channel.send(embed=discord.Embed(description="❌ invalid. round lost.", color=discord.Color.red()))
            return
        deck = make_deck()
        flipped = deck.pop()
        actual = "red" if is_red(flipped) else "black"
        emoji = "🔴" if actual == "red" else "⚫"
        await channel.send(embed=discord.Embed(description=f"{emoji} **{flipped[0]}{flipped[1]}** - **{actual}**", color=discord.Color.dark_gold()))
        if choice == actual:
            wins += 1
            await channel.send(embed=discord.Embed(description=f"✅ correct.", color=discord.Color.green()))
        else:
            losses += 1
            await channel.send(embed=discord.Embed(description=f"❌ wrong!! it was **{actual}**.", color=discord.Color.red()))

    async def do_high_or_low(rnd):
        nonlocal wins, losses
        await channel.send(embed=discord.Embed(
            title=f"🃏 round {rnd}/{ROUNDS_TOTAL}\n{scoreline(wins,losses,rnd)}",
            description="type `high` *(above 7)* or `low` *(below 7)* *8 seconds*\n*7 = push, replays once*",
            color=discord.Color.dark_gold()
        ))
        for attempt in range(2):
            try:
                msg = await bot.wait_for("message", timeout=8, check=check)
                choice = msg.content.lower().strip()
            except asyncio.TimeoutError:
                choice = ""
            if choice not in ("high", "low"):
                losses += 1
                await channel.send(embed=discord.Embed(description="❌ invalid. round lost.", color=discord.Color.red()))
                return
            deck = make_deck()
            cut = deck.pop()
            val = card_val(cut)
            actual = "high" if val > 7 else "low" if val < 7 else "push"
            await channel.send(embed=discord.Embed(description=f"cut: **{cut[0]}{cut[1]}** (`{val}`)", color=discord.Color.blurple()))
            if actual == "push":
                if attempt == 0:
                    await channel.send(embed=discord.Embed(description="🤝 push. replays.", color=discord.Color.orange()))
                    await asyncio.sleep(0.5)
                    await channel.send(embed=discord.Embed(description="type `high` or `low` again *8 seconds*", color=discord.Color.dark_gold()))
                    continue
                else:
                    losses += 1
                    await channel.send(embed=discord.Embed(description="🤝 pushed twice. round lost.", color=discord.Color.red()))
                    return
            elif choice == actual:
                wins += 1
                await channel.send(embed=discord.Embed(description=f"✅ correct!! **{actual}**.", color=discord.Color.green()))
                return
            else:
                losses += 1
                await channel.send(embed=discord.Embed(description=f"❌ wrong!! it was **{actual}**.", color=discord.Color.red()))
                return

    async def do_bust_call(rnd):
        nonlocal wins, losses
        await channel.send(embed=discord.Embed(
            title=f"🃏 round {rnd}/{ROUNDS_TOTAL}\n{scoreline(wins,losses,rnd)}",
            description="dealer draws 3 cards blind.\ntype `bust` or `safe` *8 seconds*", color=discord.Color.dark_gold()
        ))
        try:
            msg = await bot.wait_for("message", timeout=8, check=check)
            choice = msg.content.lower().strip()
        except asyncio.TimeoutError:
            choice = ""
        if choice not in ("bust", "safe"):
            losses += 1
            await channel.send(embed=discord.Embed(description="❌ invalid. round lost.", color=discord.Color.red()))
            return
        deck = make_deck()
        dealer_cards = [deck.pop() for _ in range(3)]
        dealer_total = hand_total(dealer_cards)
        busted = dealer_total > 21
        correct = "bust" if busted else "safe"
        cards_str = "  ".join(f"{c[0]}{c[1]}" for c in dealer_cards)
        await channel.send(embed=discord.Embed(description=f"dealer: **{cards_str}** -> `{dealer_total}`", color=discord.Color.blurple()))
        if choice == correct:
            wins += 1
            await channel.send(embed=discord.Embed(description=f"✅ **{correct}**!! correct.", color=discord.Color.green()))
        else:
            losses += 1
            await channel.send(embed=discord.Embed(description=f"❌ wrong!! it was **{correct}**.", color=discord.Color.red()))

    async def do_pair_spotter(rnd):
        nonlocal wins, losses
        deck = make_deck()
        dealt = [deck.pop() for _ in range(6)]
        has_pair = len([c[0] for c in dealt]) != len(set(c[0] for c in dealt))
        correct = "yes" if has_pair else "no"
        embed = discord.Embed(title=f"🃏 round {rnd}/{ROUNDS_TOTAL}\n{scoreline(wins,losses,rnd)}", description="watch the cards...", color=discord.Color.dark_gold())
        msg = await channel.send(embed=embed)
        for i, card in enumerate(dealt, 1):
            embed.description = f"**{i}/6** → {card[0]}{card[1]}"
            await msg.edit(embed=embed)
            await asyncio.sleep(0.9)
        embed.description = f"was there a **pair**?\ntype `yes` or `no` *5 seconds*\n\n{scoreline(wins,losses,rnd)}"
        await msg.edit(embed=embed)
        try:
            reply = await bot.wait_for("message", timeout=5, check=check)
            choice = reply.content.lower().strip()
        except asyncio.TimeoutError:
            choice = ""
        shown = "  ".join(f"{c[0]}{c[1]}" for c in dealt)
        if choice == correct:
            wins += 1
            await channel.send(embed=discord.Embed(description=f"✅ correct!! `{shown}` {'had' if has_pair else 'had no'} pair.", color=discord.Color.green()))
        else:
            losses += 1
            await channel.send(embed=discord.Embed(description=f"❌ wrong!! `{shown}` {'had a pair' if has_pair else 'had no pair'}.", color=discord.Color.red()))

    async def do_final_hand(rnd):
        nonlocal wins, losses
        deck = make_deck()
        player = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        ptotal = hand_total(player)
        soft = is_soft(player)
        soft_tag = " *(soft)*" if soft else ""
        await channel.send(embed=discord.Embed(
            title=f"🃏 round {rnd}/{ROUNDS_TOTAL}\n{scoreline(wins,losses,rnd)}",
            description=(
                f"**your hand:** {hand_str(player)} → `{ptotal}`{soft_tag}\n"
                f"**dealer shows:** {dealer_hand[0][0]}{dealer_hand[0][1]} + 🂠\n\n"
                f"type `hit`, `stand`, or `surrender` *8 seconds*"
            ), color=discord.Color.gold()
        ))
        try:
            msg = await bot.wait_for("message", timeout=8, check=check)
            choice = msg.content.lower().strip()
        except asyncio.TimeoutError:
            choice = "stand"
        if choice == "surrender":
            losses += 1
            await channel.send(embed=discord.Embed(description="🏳️ surrendered. round lost.", color=discord.Color.red()))
            return
        if choice == "hit":
            drawn = deck.pop()
            player.append(drawn)
            ptotal = hand_total(player)
            await channel.send(embed=discord.Embed(description=f"drew `{drawn[0]}{drawn[1]}` → `{ptotal}`", color=discord.Color.blurple()))
            if ptotal > 21:
                losses += 1
                await channel.send(embed=discord.Embed(description=f"💥 bust. round lost.", color=discord.Color.red()))
                return
        while hand_total(dealer_hand) < 17:
            dealer_hand.append(deck.pop())
        dtotal = hand_total(dealer_hand)
        await channel.send(embed=discord.Embed(description=f"dealer: {hand_str(dealer_hand)} → `{dtotal}`", color=discord.Color.blurple()))
        if dtotal > 21 or ptotal > dtotal:
            wins += 1
            await channel.send(embed=discord.Embed(description=f"✅ you win!! `{ptotal}` beats `{dtotal}`.", color=discord.Color.green()))
        elif ptotal == dtotal:
            losses += 1
            await channel.send(embed=discord.Embed(description=f"🤝 push. house takes ties. round lost.", color=discord.Color.red()))
        else:
            losses += 1
            await channel.send(embed=discord.Embed(description=f"❌ dealer wins....... `{dtotal}` beats `{ptotal}`.", color=discord.Color.red()))

    schedule = [
        ("S",1),("R",2),("S",3),("H",4),("B",5),("R",6),("P",7),("C",8),
        ("S",9),("R",10),("B",11),("H",12),("S",13),("R",14),("F",15),
    ]

    for kind, rnd in schedule:
        remaining = ROUNDS_TOTAL - rnd + 1
        if wins + remaining < ROUNDS_NEEDED:
            return False
        await asyncio.sleep(0.5)
        if kind == "S": await do_basic_strategy(rnd, blind=False)
        elif kind == "B": await do_basic_strategy(rnd, blind=True)
        elif kind == "R": await do_red_or_black(rnd)
        elif kind == "H": await do_high_or_low(rnd)
        elif kind == "P": await do_pair_spotter(rnd)
        elif kind == "C": await do_bust_call(rnd)
        elif kind == "F": await do_final_hand(rnd)
        await asyncio.sleep(0.5)

    return wins >= ROUNDS_NEEDED


async def run_socrates_escape(bot, channel, member) -> bool:
    QUESTIONS_TOTAL = 25
    QUESTIONS_NEEDED = 20
    TIME_LIMIT = 20

    def check(m):
        return m.author.id == member.id and m.channel == channel

    pool = list(SOCRATES_QUESTIONS)
    random.shuffle(pool)
    selected = pool[:QUESTIONS_TOTAL]
    correct = 0

    for i, (q_type, question, options, answer) in enumerate(selected, 1):
        remaining_needed    = QUESTIONS_NEEDED - correct
        remaining_questions = QUESTIONS_TOTAL - i + 1
        if remaining_needed > remaining_questions:
            return False

        if q_type == "mc":
            opts_str = "\n".join(f"`{k}` {v}" for k, v in options.items())
            desc = f"*\"{question}\"*\n\n{opts_str}\n\n*{TIME_LIMIT} seconds*"
        else:
            desc = f"*\"{question}\"*\n\n`true` or `false`\n\n*{TIME_LIMIT} seconds*"

        await channel.send(embed=discord.Embed(
            title=f"🏛️ QUESTION {i}/{QUESTIONS_TOTAL} -  {correct} correct",
            description=desc, color=discord.Color.from_rgb(180, 150, 80)
        ))

        try:
            msg = await bot.wait_for("message", timeout=TIME_LIMIT, check=check)
            player_answer = msg.content.lower().strip()
        except asyncio.TimeoutError:
            player_answer = ""

        if player_answer == answer:
            correct += 1
            await channel.send(embed=discord.Embed(description="✅ correct.", color=discord.Color.green()))
        else:
            if q_type == "mc":
                await channel.send(embed=discord.Embed(description=f"❌ wrong. answer was `{answer}` {options[answer]}.", color=discord.Color.red()))
            else:
                await channel.send(embed=discord.Embed(description=f"❌ wrong. answer was `{answer}`.", color=discord.Color.red()))

        await asyncio.sleep(0.5)

    return correct >= QUESTIONS_NEEDED

SP_QUESTIONS = [
    ("tf","the allegory of the cave appears in plato's republic.",None,"true"),
    ("tf","socrates claimed that he was the wisest man alive.",None,"false"),
    ("tf","plato founded the academy in athens.",None,"true"),
    ("tf","socrates served as a general in the athenian army.",None,"false"),
    ("tf","the socratic method relies on questioning to expose contradictions.",None,"true"),
    ("tf","socrates believed that the body was more important than the soul.",None,"false"),
    ("tf","xenophon wrote about socrates in his memorabilia.",None,"true"),
    ("tf","socrates was born in sparta.",None,"false"),
    ("tf","dialectic is another name for the socratic method.",None,"true"),
    ("tf","socrates believed that no one does evil willingly.",None,"true"),
    ("tf","aristotle was a direct student of socrates.",None,"false"),
    ("tf","hemlock is a type of poison derived from a plant.",None,"true"),
    ("tf","socrates escaped from prison before his execution.",None,"false"),
    ("tf","plato's symposium is about the nature of love.",None,"true"),
    ("tf","socrates believed democracy was the best form of government.",None,"false"),
    ("mc","what is the name of the socratic dialogue describing socrates' trial?",{"a":"phaedo","b":"apology","c":"meno","d":"crito"},"b"),
    ("mc","which concept describes plato's idea that objects are imperfect copies of perfect forms?",{"a":"empiricism","b":"the allegory","c":"theory of forms","d":"the dialectic"},"c"),
    ("mc","what does 'elenchus' refer to in socratic philosophy?",{"a":"a form of prayer","b":"cross-examination to reveal ignorance","c":"a type of virtue","d":"death of the soul"},"b"),
    ("mc","socrates used 'daimonion' to describe what?",{"a":"his enemies","b":"an inner divine voice","c":"a demon","d":"the state of athens"},"b"),
    ("mc","in plato's phaedo, where does the dialogue take place?",{"a":"the agora","b":"the academy","c":"socrates' prison cell","d":"the parthenon"},"c"),
    ("mc","socrates described himself as what in relation to athens?",{"a":"king","b":"gadfly","c":"shepherd","d":"doctor"},"b"),
    ("mc","what is 'aporia' in socratic dialogue?",{"a":"certainty","b":"a written treatise","c":"a state of puzzlement","d":"a type of logic"},"c"),
    ("mc","which work features socrates discussing immortality before his death?",{"a":"republic","b":"phaedrus","c":"phaedo","d":"timaeus"},"c"),
    ("mc","socrates compared his philosophical role to which profession?",{"a":"soldier","b":"midwife","c":"judge","d":"priest"},"b"),
    ("mc","plato's 'meno' primarily explores which concept?",{"a":"justice","b":"whether virtue can be taught","c":"existence of gods","d":"ideal government"},"b"),
    ("mc","what does socrates say about death in the apology?",{"a":"it is certain suffering","b":"it may be a blessing","c":"it must be feared","d":"it ends the soul"},"b"),
    ("mc","which philosopher wrote 'clouds', a comedy mocking socrates?",{"a":"euripides","b":"sophocles","c":"aristophanes","d":"aeschylus"},"c"),
    ("mc","what was the official charge that led to socrates' execution?",{"a":"treason","b":"impiety and corrupting the youth","c":"theft","d":"heresy"},"b"),
    ("mc","what was the name of socrates' famously difficult wife?",{"a":"xanthippe","b":"aspasia","c":"diotima","d":"penelope"},"a"),
    ("mc","socrates wrote which of the following?",{"a":"the republic","b":"the apology","c":"the symposium","d":"nothing"},"d"),
    ("mc","which of these was NOT one of socrates' students?",{"a":"plato","b":"alcibiades","c":"aristotle","d":"xenophon"},"c"),
    ("mc","socrates lived in which century BC?",{"a":"3rd","b":"4th","c":"5th","d":"6th"},"c"),
    ("mc","'the unexamined life is not worth living.' socrates said this at his what?",{"a":"wedding","b":"trial","c":"execution","d":"birth"},"b"),
    ("mc","socrates' method of inquiry is best described as?",{"a":"lecturing","b":"writing dialogues","c":"questioning assumptions","d":"empirical testing"},"c"),
]

MIND_CRUSH_QUOTES = [
    ("the unexamined life is not worth","living"),
    ("i know that i know","nothing"),
    ("wonder is the beginning of","wisdom"),
    ("be as you wish to","seem"),
    ("to find yourself think for","yourself"),
    ("education is the kindling of a","flame"),
    ("strong minds discuss ideas average minds discuss","events"),
]

YETI_ATTACKS = [
    ("🧊 ICE WALL: it expands violently", "react", ["shatter","dodge"]),

    ("❄️ FREEZE BREATH: he inhales deeply", "react", ["run","shield"]),

    ("🪨 BOULDER FEINT: he raises his arm... then pauses", "feint", ["wait"]),

    ("🐾 CLAW SWIPE: sudden double strike", "chain", ["block roll","roll block"]),

    ("❄️ BLIZZARD SPIN: visibility drops to zero", "react", ["curl"]),

    ("🦷 BITE: he hesitates before lunging", "timed", ["dodge","push"]),
]

async def run_socrates_prime(bot, channel, member) -> bool:
    TOTAL,NEEDED,TL,CE = 35,30,12,7
    def check(m): return m.author.id==member.id and m.channel==channel
    await channel.send(embed=discord.Embed(
        title="SOCRATES PRIME",
        description=(
            f"the legend at his prime form.\n\n"
            f"answer **{NEEDED}/{TOTAL}** correctly. **{TL}s** per question.\n"
            "multiple choice: type `a` `b` `c` `d` - true/false: type `true` or `false`"
        ),color=discord.Color.from_rgb(80,0,120)
    ))
    await asyncio.sleep(2)
    pool=list(SP_QUESTIONS); random.shuffle(pool); selected=pool[:TOTAL]; correct=0
    for i,(qt,question,options,answer) in enumerate(selected,1):
        if i>1 and (i-1)%CE==0:
            fragment,final_word=random.choice(MIND_CRUSH_QUOTES)
            shown=fragment
            await channel.send(embed=discord.Embed(title="🧠 QUOTE",
                description=f"*\"{shown}\"*\n\ntype the **final word**. 8s. fail = -3 correct. current: **{correct}**",
                color=discord.Color.from_rgb(120,0,80)))
            try:
                msg=await bot.wait_for("message",timeout=8,check=check)
                ans=msg.content.lower().strip()
            except asyncio.TimeoutError: ans=""
            if ans==final_word:
                await channel.send(embed=discord.Embed(description="✅ correct quote.",color=discord.Color.green()))
            else:
                correct=max(0,correct-3)
                await channel.send(embed=discord.Embed(description=f"💀 wrong. answer: **{final_word}**. lost 3. ({correct} remaining)",color=discord.Color.dark_red()))
            await asyncio.sleep(0.8)
        if (NEEDED-correct)>(TOTAL-i+1): return False
        if qt=="mc":
            desc=f"*\"{question}\"*\n\n"+"\n".join(f"`{k}` {v}" for k,v in options.items())+f"\n\n*{TL}s*"
        else:
            desc=f"*\"{question}\"*\n\n`true` or `false`\n\n*{TL}s*"
        await channel.send(embed=discord.Embed(title=f"👁️ PRIME - Q {i}/{TOTAL}  -  {correct} correct",description=desc,color=discord.Color.from_rgb(80,0,120)))
        try:
            msg=await bot.wait_for("message",timeout=TL,check=check)
            pa=msg.content.lower().strip()
        except asyncio.TimeoutError: pa=""
        if pa==answer:
            correct+=1
            await channel.send(embed=discord.Embed(description="✅ correct.",color=discord.Color.green()))
        else:
            suffix=f" {options[answer]}" if qt=="mc" else ""
            await channel.send(embed=discord.Embed(description=f"❌ wrong. answer: `{answer}`{suffix}.",color=discord.Color.red()))
        await asyncio.sleep(0.4)
    return correct>=NEEDED


async def run_yeti_fight(bot, channel, member) -> bool:
    def check(m):
        return m.author.id == member.id and m.channel == channel

    await channel.send(embed=discord.Embed(
        title="🦣 THE YETI",
        description=(
            "`(shatter/run/wait/block roll/curl/dodge)`"
        ),
        color=discord.Color.from_rgb(180,230,255)
    ))

    await asyncio.sleep(2)

    misses = 0

    for r, (attack, mode, valid) in enumerate(random.sample(YETI_ATTACKS, 5), 1):

        await channel.send(embed=discord.Embed(
            description=f"**round {r}/5**\n\n{attack}",
            color=discord.Color.from_rgb(180,230,255)
        ))

        try:
            msg = await bot.wait_for("message", timeout=6, check=check)
            ans = msg.content.lower().strip()
        except asyncio.TimeoutError:
            ans = ""

        if mode == "feint":
            if ans == "":
                await channel.send("🧠 *you read the feint.*")
            else:
                misses += 1
                await channel.send(f"💥 you reacted to nothing ({misses}/2)")

        elif mode == "chain":
            if any(v in ans for v in valid):
                await channel.send("⚡ clean chain response")
            else:
                misses += 1
                await channel.send(f"💥 broken chain ({misses}/2)")

        elif mode == "timed":
            if ans in valid:
                await channel.send("✅ precise dodge")
            else:
                misses += 1
                await channel.send(f"❄️ hit ({misses}/2)")

        else:
            if ans in valid:
                await channel.send("✅ dodged!")
            else:
                misses += 1
                await channel.send(f"💥 hit ({misses}/2)")

        if misses >= 2:
            await channel.send(embed=discord.Embed(
                title="💀 FROZEN",
                description="the yeti overwhelms your reactions.",
                color=discord.Color.blue()
            ))
            return False

        await asyncio.sleep(0.4)

    return True

class SocratesPrimeView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60); self.bot=bot

    @discord.ui.button(label="face socrates prime",style=discord.ButtonStyle.danger)
    async def engage(self, interaction: discord.Interaction, button: discord.ui.Button):
        member=interaction.user; channel=interaction.channel
        async with db.pool.acquire() as conn:
            already=await conn.fetchval("SELECT spark_of_hatred FROM user_unlocks WHERE user_id=$1",member.id)
        if already:
            return await interaction.response.send_message("you've already defeated socrates prime. the spark of hatred is yours.",ephemeral=True)
        self.stop()
        await interaction.response.send_message(embed=discord.Embed(description="*the prime intellect stirs.*\n35 questions (need 30) with 12s each\nquotes every 7 questions",color=discord.Color.from_rgb(80,0,120)),ephemeral=True)
        result=await run_socrates_prime(self.bot,channel,member)
        if result:
            async with db.pool.acquire() as conn:
                await conn.execute("INSERT INTO user_unlocks (user_id,spark_of_hatred) VALUES ($1,TRUE) ON CONFLICT (user_id) DO UPDATE SET spark_of_hatred=TRUE",member.id)
            await channel.send(embed=discord.Embed(title="SOCRATES PRIME YIELDS",
                description=f"**{member.mention}** answered his questions right.\n\n⚡ **spark of hatred obtained**: `!craft key`",
                color=discord.Color.from_rgb(80,0,120)))
            await hooks.on_socrates_prime_defeat(self.bot,member)
        else:
            await channel.send(embed=discord.Embed(title="HUNG, DRAWN AND QUARTERED",description=f"**{member.mention}** could not withstand the might.",color=discord.Color.dark_purple()))


class YetiFightView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60); self.bot=bot

    @discord.ui.button(label="fight the yeti",style=discord.ButtonStyle.danger,emoji="🦣")
    async def engage(self, interaction: discord.Interaction, button: discord.ui.Button):
        member=interaction.user; channel=interaction.channel
        async with db.pool.acquire() as conn:
            row=await conn.fetchrow("SELECT last_fight FROM enemy_cooldowns WHERE user_id=$1 AND enemy='yeti'",member.id)
        if row:
            ce=row["last_fight"]+timedelta(hours=48)
            if ce>dt.now(timezone.utc):
                return await interaction.response.send_message(f"❄️ yeti recovering. try again **<t:{int(ce.timestamp())}:R>**",ephemeral=True)
        self.stop()
        await interaction.response.send_message(embed=discord.Embed(description="❄️ **the yeti charges...**",color=discord.Color.from_rgb(180,230,255)),ephemeral=True)
        result=await run_yeti_fight(self.bot,channel,member)
        if result:
            async with db.pool.acquire() as conn:
                already=await conn.fetchval("SELECT snow_globe FROM user_unlocks WHERE user_id=$1",member.id)
                if not already:
                    await conn.execute("INSERT INTO user_unlocks (user_id,snow_globe) VALUES ($1,TRUE) ON CONFLICT (user_id) DO UPDATE SET snow_globe=TRUE",member.id)
                    globe_msg="\n❄️ **snow globe obtained**: `!craft key`"
                else: globe_msg="\n❄️ you already have the snow globe."
            await channel.send(embed=discord.Embed(title="🏆 YETI DEFEATED",description=f"**{member.mention}** took down the yeti!{globe_msg}",color=discord.Color.from_rgb(180,230,255)))
            await hooks.on_yeti_defeat(self.bot,member)
            async with db.pool.acquire() as conn:
                await conn.execute("INSERT INTO enemy_cooldowns (user_id,enemy,last_fight) VALUES ($1,'yeti',$2) ON CONFLICT (user_id,enemy) DO UPDATE SET last_fight=EXCLUDED.last_fight",member.id,dt.now(timezone.utc))
        else:
            await channel.send(embed=discord.Embed(title="💀 FROZEN SOLID",description=f"**{member.mention}** was frozen solid.",color=discord.Color.blue()))

class MinneapolisFightView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    @discord.ui.button(label="the dealer", style=discord.ButtonStyle.danger, emoji="🃏")
    async def dealer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="",
                description=(
                    "**🃏 the dealer**\n\n"
                    "beat him at cards, if you know what you're doing.\n"
                ),
                color=discord.Color.dark_gold()
            ),
            view=HouseGameView(self.bot)
        )

SOCRATES_QUESTIONS = [
    ("mc", "what did socrates famously claim to know?",
     {"a": "everything about philosophy", "b": "nothing", "c": "the nature of the gods", "d": "the secrets of the afterlife"}, "b"),

    ("mc", "socrates was sentenced to death in which city?",
     {"a": "sparta", "b": "corinth", "c": "athens", "d": "thebes"}, "c"),

    ("mc", "what did socrates drink to carry out his death sentence?",
     {"a": "wine", "b": "water", "c": "hemlock", "d": "vinegar"}, "c"),

    ("mc", "who wrote most of what we know about socrates?",
     {"a": "aristotle", "b": "plato", "c": "homer", "d": "herodotus"}, "b"),

    ("mc", "what was socrates charged with?",
     {"a": "treason and murder", "b": "theft and fraud", "c": "impiety and corrupting the youth", "d": "desertion from the army"}, "c"),

    ("mc", "socrates compared his role in athens to what creature?",
     {"a": "a lion", "b": "a serpent", "c": "an eagle", "d": "a gadfly"}, "d"),

    ("mc", "what did the oracle at delphi say about socrates?",
     {"a": "that he was the bravest man alive", "b": "that no man was wiser", "c": "that he would outlive all kings", "d": "that he was favoured by zeus"}, "b"),

    ("mc", "socrates believed that virtue is identical to what?",
     {"a": "wealth", "b": "strength", "c": "knowledge", "d": "piety"}, "c"),

    ("mc", "which of these best describes the socratic method?",
     {"a": "writing long philosophical texts", "b": "memorising the works of homer", "c": "examining beliefs through dialogue and questioning", "d": "performing religious rituals"}, "c"),

    ("mc", "in plato's allegory of the cave, the shadows on the wall represent what?",
     {"a": "the gods", "b": "false appearances and illusions", "c": "the souls of the dead", "d": "mathematical truths"}, "b"),

    ("mc", "socrates believed that wrongdoing is caused by what?",
     {"a": "evil nature", "b": "bad upbringing", "c": "ignorance", "d": "poverty"}, "c"),

    ("mc", "what term describes socrates pretending ignorance to expose flaws in others' thinking?",
     {"a": "sophistry", "b": "rhetoric", "c": "socratic irony", "d": "dialectical realism"}, "c"),

    ("mc", "which philosopher was directly taught by socrates?",
     {"a": "aristotle", "b": "plato", "c": "epicurus", "d": "zeno"}, "b"),

    ("mc", "socrates lived in which century BC?",
     {"a": "3rd", "b": "7th", "c": "5th", "d": "1st"}, "c"),

    ("mc", "what is elenchus?",
     {"a": "a type of greek pottery", "b": "a method of cross-examination to test beliefs", "c": "a form of military training", "d": "a style of epic poetry"}, "b"),

    ("mc", "socrates wrote which of the following?",
     {"a": "the republic", "b": "the nicomachean ethics", "c": "nothing. he only spoke", "d": "the apology"}, "c"),

    ("mc", "the unexamined life is not worth living. socrates said this at his what?",
     {"a": "wedding", "b": "trial", "c": "funeral", "d": "graduation"}, "b"),

    ("mc", "which of these was NOT one of socrates' students?",
     {"a": "plato", "b": "alcibiades", "c": "xenophon", "d": "pythagoras"}, "d"),

    ("mc", "socrates' wife was famously described as difficult. what was her name?",
     {"a": "penelope", "b": "xanthippe", "c": "medea", "d": "aspasia"}, "b"),

    ("mc", "what is the ship of theseus paradox about?",
     {"a": "the speed of ships", "b": "whether identity persists when all parts are replaced", "c": "the navigation of the aegean sea", "d": "the strength of wooden hulls"}, "b"),

    ("tf", "socrates wrote down his own philosophy in books.", None, "false"),

    ("tf", "plato was a student of socrates.", None, "true"),

    ("tf", "socrates believed the soul was mortal and died with the body.", None, "false"),

    ("tf", "socrates accepted money for his teachings.", None, "false"),

    ("tf", "aristotle was taught directly by socrates.", None, "false"),

    ("tf", "socrates fought as a soldier for athens.", None, "true"),

    ("tf", "the socratic method involves asking questions to reveal contradictions.", None, "true"),

    ("tf", "socrates was found innocent at his trial.", None, "false"),

    ("tf", "socrates believed that no one does wrong willingly.", None, "true"),

    ("tf", "plato's republic was written by socrates himself.", None, "false"),

    ("tf", "the oracle at delphi said socrates was the wisest man alive.", None, "true"),

    ("tf", "socrates lived to the age of 90.", None, "false"),

    ("tf", "socrates believed that the unexamined life is not worth living.", None, "true"),

    ("tf", "socrates was born in sparta.", None, "false"),

    ("tf", "the allegory of the cave appears in plato's republic.", None, "true"),
]


class SocratesView(discord.ui.View):
    QUESTIONS_TOTAL = 25
    QUESTIONS_NEEDED = 20
    TIME_LIMIT = 20

    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    @discord.ui.button(label="answer socrates", style=discord.ButtonStyle.primary, emoji="\U0001f3db\ufe0f")
    async def engage(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        channel = interaction.channel

        async with db.pool.acquire() as conn:
            already_won = await conn.fetchval(
                "SELECT philosopher_soul FROM user_unlocks WHERE user_id=$1", member.id
            )

        if already_won:
            return await interaction.response.send_message(
                "you've already bested socrates. the philosopher's soul is yours.",
                ephemeral=True
            )

        self.stop()
        await interaction.response.send_message(
            embed=discord.Embed(
                description=(
                    "*socrates steps forward.*\n"
                    "*\"i shall question you. answer wisely.\"\n\n"
                    f"*{self.QUESTIONS_TOTAL} questions - need {self.QUESTIONS_NEEDED} correct "
                    f"{self.TIME_LIMIT}s each*\n"
                    "multiple choice: type `a` `b` `c` `d` - true/false: type `true` or `false`*"
                ),
                color=discord.Color.from_rgb(180, 150, 80)
            ),
            ephemeral=True
        )

        def check(m):
            return m.author.id == member.id and m.channel == channel

        pool = list(SOCRATES_QUESTIONS)
        random.shuffle(pool)
        selected = pool[:self.QUESTIONS_TOTAL]

        correct = 0

        for i, (q_type, question, options, answer) in enumerate(selected, 1):
            remaining_needed    = self.QUESTIONS_NEEDED - correct
            remaining_questions = self.QUESTIONS_TOTAL - i + 1

            if remaining_needed > remaining_questions:
                await channel.send(embed=discord.Embed(
                    title="\U0001f3db\ufe0f SOCRATES WINS",
                    description=(
                        f"**{member.mention}** can no longer reach {self.QUESTIONS_NEEDED} correct.\n"
                        f"score: `{correct}/{self.QUESTIONS_TOTAL}`"
                    ),
                    color=discord.Color.dark_red()
                ))
                return

            if q_type == "mc":
                opts_str = "\n".join(f"`{k}` {v}" for k, v in options.items())
                desc = f"*\"{question}\"*\n\n{opts_str}\n\n*{self.TIME_LIMIT} seconds*"
            else:
                desc = f"*\"{question}\"*\n\n`true` or `false`\n\n*{self.TIME_LIMIT} seconds*"

            await channel.send(embed=discord.Embed(
                title=f"\U0001f3db\ufe0f QUESTION {i}/{self.QUESTIONS_TOTAL}  -  {correct} correct",
                description=desc,
                color=discord.Color.from_rgb(180, 150, 80)
            ))

            try:
                msg = await self.bot.wait_for("message", timeout=self.TIME_LIMIT, check=check)
                player_answer = msg.content.lower().strip()
            except asyncio.TimeoutError:
                player_answer = ""

            if player_answer == answer:
                correct += 1
                await channel.send(embed=discord.Embed(
                    description="\u2705 correct.",
                    color=discord.Color.green()
                ))
            else:
                if q_type == "mc":
                    correct_text = options[answer]
                    await channel.send(embed=discord.Embed(
                        description=f"\u274c wrong!! the answer was `{answer}` {correct_text}.",
                        color=discord.Color.red()
                    ))
                else:
                    await channel.send(embed=discord.Embed(
                        description=f"\u274c wrong!! the answer was `{answer}`.",
                        color=discord.Color.red()
                    ))

            await asyncio.sleep(0.6)

        if correct >= self.QUESTIONS_NEEDED:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_unlocks (user_id, philosopher_soul)
                    VALUES ($1, TRUE)
                    ON CONFLICT (user_id) DO UPDATE SET philosopher_soul = TRUE
                    """,
                    member.id
                )

            from cogs.achievements import hooks
            await hooks.on_socrates_defeat(self.bot, member)

            await channel.send(embed=discord.Embed(
                title="\U0001f3db\ufe0f SOCRATES YIELDS",
                description=(
                    f"**{member.mention}** answered {correct}/{self.QUESTIONS_TOTAL} correctly.\n\n"
                    "\"it seems you know something after all.\"\n\n"
                    "\U0001f52e **philosopher's soul obtained**. craft the dreamsky trident with `!craft trident`."
                ),
                color=discord.Color.from_rgb(180, 150, 80)
            ))
        else:
            await channel.send(embed=discord.Embed(
                title="\U0001f3db\ufe0f SOCRATES WINS",
                description=(
                    f"**{member.mention}** answered {correct}/{self.QUESTIONS_TOTAL} correctly.\n"
                    f"needed {self.QUESTIONS_NEEDED}.\n\n"
                    "*\"the only true wisdom is knowing you know nothing.\"*"
                ),
                color=discord.Color.dark_red()
            ))

class FightView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    @discord.ui.button(label="fight vladurk", style=discord.ButtonStyle.danger)
    async def fight_vlad(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        channel = interaction.channel
        solves = 0

        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT last_fight FROM enemy_cooldowns WHERE user_id=$1 AND enemy=$2",
                member.id,
                "vladurk"
            )

        if row:
            cooldown_end = row["last_fight"] + timedelta(hours=24)

            if cooldown_end > dt.now(timezone.utc):
                ts = int(cooldown_end.timestamp())

                return await interaction.response.send_message(
                    f"⏳ you already fought **vladurk** today.\n"
                    f"come back **<t:{ts}:R>**",
                    ephemeral=True
                )

        await interaction.response.send_message(
            embed=discord.Embed(
                description="⚔️ **the fight against vladurk begins...**",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

        for _ in range(PUZZLE_COUNT):
            puzzle_type = random.choice([
                "scramble",
                "math",
                "pattern",
                "riddle",
                "reverse",
                "memory",
                "elimination"
            ])

            if puzzle_type == "scramble":
                word = random.choice(SCRAMBLE_WORDS)
                scrambled = "".join(random.sample(word, len(word)))
                await channel.send(embed=discord.Embed(
                    description=f"🧩 **unscramble this word:** `{scrambled}`",
                    color=discord.Color.blue()
                ))
                answer = word

            elif puzzle_type == "math":
                q, a = random.choice(MATH_QUESTIONS)
                await channel.send(embed=discord.Embed(
                    description=f"🧠 **solve the math:** `{q}`",
                    color=discord.Color.blue()
                ))
                answer = str(a)

            elif puzzle_type == "pattern":
                q, a = random.choice(PATTERN_QUESTIONS)
                await channel.send(embed=discord.Embed(
                    description=f"🔢 **complete the pattern:** `{q}`",
                    color=discord.Color.blue()
                ))
                answer = a

            elif puzzle_type == "riddle":
                q, a = random.choice(RIDDLES)
                await channel.send(embed=discord.Embed(
                    description=f"❓ **riddle:** {q}",
                    color=discord.Color.blue()
                ))
                answer = a

            elif puzzle_type == "reverse":
                q, a = random.choice(REVERSE_WORDS)
                await channel.send(embed=discord.Embed(
                    description=f"🔁 **reverse this word:** `{q}`",
                    color=discord.Color.blue()
                ))
                answer = a

            elif puzzle_type == "memory":
                seq = random.choice(MEMORY_SEQUENCES)

                emoji_to_word = {
                    "🟥": "red",
                    "🟦": "blue",
                    "🟩": "green",
                    "🟨": "yellow"
                }

                embed = discord.Embed(
                    description="🧠 **memorize the sequence...**",
                    color=discord.Color.blue()
                )

                msg = await channel.send(embed=embed)

                for i, emoji in enumerate(seq, start=1):
                    embed.description = f"🧠 **memorize the sequence...**\n\n**{i}** - {emoji}"
                    await msg.edit(embed=embed)
                    await asyncio.sleep(1)

                await asyncio.sleep(1)

                embed.description = (
                    "🧠 **now type the colors in order!**\n"
                    "example: `red blue green yellow`"
                )
                await msg.edit(embed=embed)

                answer = " ".join(emoji_to_word[e] for e in seq)

            elif puzzle_type == "elimination":
                options, correct = random.choice(WORD_ELIMINATION)
                option_str = ", ".join(options)
                await channel.send(embed=discord.Embed(
                    description=f"❌ **which one doesn't belong?**\noptions: {option_str}",
                    color=discord.Color.blue()
                ))
                answer = correct

            def check(m):
                return m.author.id == member.id and m.channel == channel

            try:
                msg = await self.bot.wait_for("message", timeout=TIME_LIMIT, check=check)
                if msg.content.lower() == answer.lower():
                    solves += 1
                    await channel.send(embed=discord.Embed(
                        description="✅ correct!",
                        color=discord.Color.green()
                    ))
                else:
                    await channel.send(embed=discord.Embed(
                        description=f"❌ wrong! answer was **{answer}**",
                        color=discord.Color.red()
                    ))
            except asyncio.TimeoutError:
                await channel.send(embed=discord.Embed(
                    description=f"⏰ time's up! answer was **{answer}**",
                    color=discord.Color.red()
                ))

        if solves >= REQUIRED_SOLVES:

            async with db.pool.acquire() as conn:

                await conn.execute(
                    "UPDATE economy SET quid = quid + 250 WHERE user_id = $1",
                    member.id
                )

                await conn.execute(
                    """
                    INSERT INTO enemy_cooldowns (user_id, enemy, last_fight)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id, enemy)
                    DO UPDATE SET last_fight = EXCLUDED.last_fight
                    """,
                    member.id,
                    "vladurk",
                    dt.now(timezone.utc)
                )

            await channel.send(embed=discord.Embed(
                description=f"🏆 **{member.mention} defeated vladurk!**\n💰 reward: **250 quid**",
                color=discord.Color.gold()
            ))
            await hooks.on_vlad_defeat(self.bot, member)

            async with db.pool.acquire() as conn:
                already = await conn.fetchval("SELECT bone_key_cutter FROM user_unlocks WHERE user_id=$1", member.id)
                if not already:
                    await conn.execute(
                        "INSERT INTO user_unlocks (user_id, bone_key_cutter) VALUES ($1,TRUE) ON CONFLICT (user_id) DO UPDATE SET bone_key_cutter=TRUE",
                        member.id
                    )
                    await channel.send("🦴 vladurk drops a **bone key cutter**. key component obtained. (`!craft key`)")
                    await hooks.on_vladurk_drop(self.bot, member)
        else:
            await channel.send(embed=discord.Embed(
                description=f"💀 **vladurk defeated {member.mention}.** ({solves}/{PUZZLE_COUNT} solved)",
                color=discord.Color.dark_red()
            ))

class YoTopView(discord.ui.View):
    def __init__(self, bot, ctx, total_pages, page_size=5):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx
        self.page = 1
        self.total_pages = total_pages
        self.page_size = page_size

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "this leaderboard isn't for you lil bro",
                ephemeral=True
            )
            return False
        return True

    async def generate_embed(self):
        skip = (self.page - 1) * self.page_size

        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, yo_count
                FROM yo_user
                ORDER BY yo_count DESC
                OFFSET $1 LIMIT $2
                """,
                skip, self.page_size
            )

        def rank_emoji(pos):
            if pos == 1:
                return "<:diamondvlad:1402318150028234752>"
            if pos == 2:
                return "<:goldvlad:1402318157552685159>"
            if pos == 3:
                return "<:silvervlad:1402318161461907597>"
            return "<:vlad:1402318168097165352>"

        embed = discord.Embed(
            title="yo leaderboard",
            description="who says yo the most",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=self.ctx.guild.icon)

        if not rows:
            embed.add_field(
                name="empty",
                value="no yo data on this page",
                inline=False
            )

        for idx, row in enumerate(rows, start=1):
            position = idx + (self.page_size * (self.page - 1))
            emoji = rank_emoji(position)

            user = self.ctx.guild.get_member(row["user_id"])
            if not user:
                try:
                    user = await self.bot.fetch_user(row["user_id"])
                except discord.NotFound:
                    user = None

            name = (
                user.display_name
                if user
                else f"Unknown ({row['user_id']})"
            )

            embed.add_field(
                name=f"{emoji} **#{position} - {name}**",
                value=f"**Yos:** `{row['yo_count']:,}`",
                inline=False
            )

        embed.set_footer(
            text=f"page {self.page}/{self.total_pages} - requested by {self.ctx.author.display_name}"
        )

        return embed

    @discord.ui.button(label="◀", style=discord.ButtonStyle.success)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            embed = await self.generate_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="▶", style=discord.ButtonStyle.success)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages:
            self.page += 1
            embed = await self.generate_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class QuoteToggleView(discord.ui.View):
    def __init__(
        self,
        *,
        quote: str,
        display_name: str,
        username: str,
        avatar_url: str,
        colorful: bool = False
    ):
        super().__init__(timeout=None)
        self.quote = quote
        self.display_name = display_name
        self.username = username
        self.avatar_url = avatar_url
        self.colorful = colorful

        self.toggle.label = "⚫ Colorless" if colorful else "🎨 Colorful"

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.colorful = not self.colorful
        button.label = "⚫ Colorless" if self.colorful else "🎨 Colorful"

        img = render_quote(
            quote=self.quote,
            display_name=self.display_name,
            username=self.username,
            avatar_url=self.avatar_url,
            colorful=self.colorful
        )

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        file = discord.File(fp=buffer, filename="quote.png")

        await interaction.response.edit_message(
            attachments=[file],
            view=self
        )

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}

    @commands.command(
        name="say",
        role="Admin",
        help="make me say something",
        usage="!say stuff"
    )
    @commands.has_role(AIRole)
    async def say(
        self,
        ctx: commands.Context,
        channel: typing.Optional[discord.TextChannel],
        reply_to: typing.Optional[discord.Message],
        *,
        message: str
    ):
        await ctx.message.delete()

        if reply_to:
            await reply_to.reply(message)
            return
        if channel:
            await channel.send(message)
            return

        await ctx.channel.send(message)

    @commands.command(
        name="ask",
        help="ask me something",
        usage="!ask <question>"
    )
    async def ask(self, ctx: commands.Context, *, question: str = None):
        if not question:
            return await ctx.reply("bruh ask me somethin")
        await self.run_sequence(ctx, question)

    async def run_sequence(self, ctx, question):
        q_lower = question.lower()

        try:
            if "who" in q_lower and RESP_WHO:
                response = random.choice(RESP_WHO)
            elif "when" in q_lower and RESP_WHEN:
                response = random.choice(RESP_WHEN)
            elif "what" in q_lower and RESP_WHAT:
                response = random.choice(RESP_WHAT)
            elif "why" in q_lower and RESP_WHY:
                response = random.choice(RESP_WHY)
            elif "should" in q_lower and RESP_SHOULD:
                response = random.choice(RESP_SHOULD)
            else:
                response = random.choice(RESP_ANSWERS or ["WHAT are you saying bro"])

            await ctx.reply(response)

        except Exception as e:
            print(f"[ASK ERROR] {e}")
            await ctx.reply("random ahh error idk")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        bot_mention = f"<@{self.bot.user.id}>"
        prefix = f"{bot_mention} is this true"

        if message.content.lower().startswith(prefix.lower()):
            question = message.content[len(prefix):].strip()
            ctx = await self.bot.get_context(message)
            await self.run_sequence(ctx, question)

    @commands.command(name="yocount", help="see how many times yo was said", usage="!yocount")
    async def yocount(self, ctx: commands.Context):
        try:
            async with db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT yo_count FROM yo_global WHERE word = $1",
                    "yo"
                )

            if row is None:
                await ctx.send("nobody said yo so far")
                return

            await ctx.send(f"yo has been said {row['yo_count']:,} times.")

        except Exception as e:
            print(f"[YOCOUNT ERROR] {e}")
            await ctx.send("random ahh error")

    @commands.command(
        name="yotop",
        help="check the yo leaderboard",
        usage="!yotop"
    )
    async def yotop(self, ctx):
        page_size = 5

        async with db.pool.acquire() as conn:
            total_users = await conn.fetchval(
                "SELECT COUNT(*) FROM yo_user"
            )

        if total_users == 0:
            return await ctx.send("no yo data exists yet")

        total_pages = (total_users + page_size - 1) // page_size

        view = YoTopView(
            bot=self.bot,
            ctx=ctx,
            total_pages=total_pages,
            page_size=page_size
        )

        embed = await view.generate_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(
        name="avatar",
        help="check someones pfp",
        usage="!avatar person"
    )
    async def avatar(self, ctx: commands.Context, user: typing.Optional[discord.Member]):
        if not user:
            user = ctx.author

        avatar_url = user.avatar
        if avatar_url is None:
            await ctx.reply("blub doesnt have a pfp lmfao")
            return

        if user.id != ctx.me.id:
            embed = discord.Embed(
                title=f"{user.display_name}'s pfp",
                color=discord.Color.random()
            )
        else:
            embed = discord.Embed(
                title="my pfp?!??!??",
                description="stalker creep",
                color=discord.Color.purple()
            )

        embed.set_image(url=avatar_url)
        await ctx.reply(embed=embed)

    @commands.command(
        name="meaning",
        aliases=["define", "ud"],
        help="look up a word on urban dictionary",
        usage="!meaning <word>"
    )
    async def meaning(self, ctx, *, term: str):
        url = "https://api.urbandictionary.com/v0/define"
        params = {"term": term}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return await ctx.send("urban dictionary is tweaking rn")

                data = await resp.json()

        if not data["list"]:
            return await ctx.send(f"no results found for **{term}**")

        entry = data["list"][0]

        definition = entry["definition"].replace("[", "").replace("]", "")
        example = entry["example"].replace("[", "").replace("]", "")

        embed = discord.Embed(
            title=f"📖 {entry['word']}",
            description=definition[:4096],
            color=discord.Color.blurple()
        )

        if example:
            embed.add_field(
                name="example",
                value=example[:1024],
                inline=False
            )

        embed.set_footer(
            text=f"👍 {entry['thumbs_up']} | 👎 {entry['thumbs_down']}"
        )

        await ctx.send(embed=embed)

    @commands.command(name="math", help="do meth", usage="!math <expression> | !math graph <expression>")
    async def math(self, ctx, *, expression: str):
        if not expression:
            return await ctx.send("❌ no expression")

        if expression.lower().startswith("graph "):
            expr_str = expression[6:].strip()
            return await self._graph(ctx, expr_str)

        try:
            expr = parse_expr(
                expression,
                local_dict=SAFE_GLOBALS,
                transformations=transformations,
                evaluate=True
            )

            simplified = sp.simplify(expr)

            if simplified.is_number:
                num = simplified.evalf(DECIMAL_CAP + 2)

                if num == int(num):
                    return await ctx.send(str(int(num)))

                s = f"{num:.{DECIMAL_CAP}f}".rstrip("0").rstrip(".")
                return await ctx.send(s)

            approx = simplified.evalf(DECIMAL_CAP + 2)
            s = f"{approx:.{DECIMAL_CAP}f}".rstrip("0").rstrip(".")
            await ctx.send(s)

        except Exception:
            await ctx.send("❌ invalid math expression")

    async def _graph(self, ctx, expr_str: str):
        try:
            x = sp.symbols("x")

            expr = parse_expr(
                expr_str,
                local_dict={**SAFE_GLOBALS, "x": x},
                transformations=transformations,
                evaluate=True
            )

            expr = sp.simplify(expr)

            f = sp.lambdify(x, expr, modules=["numpy"])

            xs = np.linspace(-10, 10, 1000)
            ys = f(xs)

            plt.figure()
            plt.plot(xs, ys)
            plt.axhline(0)
            plt.axvline(0)
            plt.grid(True)

            buf = BytesIO()
            plt.savefig(buf, format="png")
            plt.close()
            buf.seek(0)

            await ctx.send(file=discord.File(buf, filename="graph.png"))

        except Exception:
            await ctx.send("❌ cannot graph this expression")

    @commands.command(name="fight", help="battle enemies in your current location", usage="!fight")
    async def fight(self, ctx):
        from cogs.fishing.fishingcommands import get_hell_layer, HELL_LAYERS
        from cogs.hell.hellcommands import HellBossView
        cid = ctx.channel.id

        if cid == MINNEAPOLIS_CHANNEL:
            return await ctx.send(embed=discord.Embed(title="🃏 the dealer",description="beat him at cards, if you know what you're doing.",color=discord.Color.dark_gold()),view=HouseGameView(self.bot))

        if cid == HEAVEN_CHANNEL:
            return await ctx.send(embed=discord.Embed(title="🏛️ socrates",description="**an old man sits among the clouds, questioning everything...**\n\nanswer his questions wisely.",color=discord.Color.from_rgb(180,150,80)),view=SocratesView(self.bot))

        if cid == DREAMSKY_CHANNEL:
            if DREAMSKY_ROLE not in {r.id for r in ctx.author.roles}:
                return await ctx.send("you are not in the dream sky.")
            return await ctx.send(embed=discord.Embed(title="socrates prime",
                description="**he waited for this.**\n\n35 questions (need 30). 12 seconds each.\nquotes every 7 questions.\n\ndefeat him to obtain **spark of hatred**.\n*he can only be defeated once.*",
                color=discord.Color.from_rgb(80,0,120)),view=SocratesPrimeView(self.bot))

        if cid == ICY_PEAKS_CHANNEL:
            if ICY_PEAKS_ROLE not in {r.id for r in ctx.author.roles}:
                return await ctx.send("you are not in the icy peaks.")
            return await ctx.send(embed=discord.Embed(title="🦣 the yeti",
                description="**a massive yeti erupts from the snow.**\n\ndodge 5 attacks. miss 2 and you're frozen.\n\ndefeat it to obtain ❄️ **snow globe**.",
                color=discord.Color.from_rgb(180,230,255)),view=YetiFightView(self.bot))

        if cid == HOUSEOFVLADS_CHANNEL:
            return await ctx.send(embed=discord.Embed(title="⚔️ house of vlads",
                description="**enemies available:**\n\n🩸 **vladurk**!!!!!!!!!!!!!! solve puzzles to defeat her.\ndefeat her to obtain 🦴 **bone key cutter**.",
                color=discord.Color.dark_red()),view=FightView(self.bot))

        layer = get_hell_layer(cid)
        if layer:
            if layer["role"] not in {r.id for r in ctx.author.roles}:
                return await ctx.send("you do not have access to this layer of hell.")
            if layer["mechanic"]:
                mechanic_hints = {
                    "evil_quid": "earn 500 evil quid total through !work, !crime, or !fish in hell.",
                    "fish_discard": "use `!discard <amount>` to discard 150 fish.",
                    "greed_pool": "use `!tribute <amount>` to contribute 7,500 quid to the greed pool.",
                }
                return await ctx.send(f"⚙️ **{layer['name']}** has no boss! it's a mechanic layer.\n{mechanic_hints[layer['mechanic']]}")
            if not layer["boss"]:
                return await ctx.send("this layer has no boss.")
            boss_names = {"aphrodite":"Aphrodite","genghis_khan":"Genghis Khan","caligula":"Caligula","king_minnea":"King Minnea","dealer_sr":"Dealer Sr.","anti_vlad":"The Anti-Vlad"}
            boss_descs = {
                "aphrodite": "the goddess of love stands before you.",
                "genghis_khan": "the great khan charges from the steppe.",
                "caligula": "the mad emperor stares at you.",
                "king_minnea": "the pillager king of Minneapolis stands before you.",
                "dealer_sr": "the original dealer. the one who taught the dealer everything.",
                "anti_vlad": "you have reached the bottom.",
            }
            return await ctx.send(embed=discord.Embed(
                title=f"{layer['emoji']} {boss_names[layer['boss']]}",
                description=boss_descs[layer["boss"]],
                color=discord.Color.from_rgb(180,0,0)
            ), view=HellBossView(self.bot, layer, ctx.author))

        from cogs.economy.economycommands import TAX_COLLECTOR_CHANNEL_ID
        if TAX_COLLECTOR_CHANNEL_ID and cid == TAX_COLLECTOR_CHANNEL_ID:
            return await ctx.send(embed=discord.Embed(
                title="🧾 THE TAX COLLECTOR",
                description=(
                    "*a man in a grey suit sits behind a towering pile of ledgers.*\n\n"
                    "**\"you owe me boy lets see how much.\"**\n\n"
                    "you need a **golden receipt** from the secret shop to challenge him.\n"
                    "use `!use receipt` to start the fight."
                ),
                color=discord.Color.from_rgb(60, 60, 60)
            ))

        await ctx.send("you can only fight in house of vlads, minneapolis, heaven, the dream sky, the icy peaks, or a layer of hell.")

    @commands.command(name="ascend")
    async def ascend(self, ctx):

        if ctx.channel.id != HEAVEN_CHANNEL:
            return

        dreamsky_role = ctx.guild.get_role(DREAMSKY_ROLE)
        if dreamsky_role in ctx.author.roles:
            return

        async with db.pool.acquire() as conn:
            has_trident = await conn.fetchval(
                "SELECT 1 FROM user_owned_rods WHERE user_id=$1 AND rod_id='dreamsky_trident'",
                ctx.author.id
            )

        if not has_trident:
            return await ctx.send("🔱 you need the **dreamsky trident** to ascend.")

        await ctx.author.add_roles(dreamsky_role)

        await ctx.send(
            embed=discord.Embed(
                title="✨ THE DREAM SKY",
                description=f"**{ctx.author.display_name}** ascends beyond heaven.",
                color=discord.Color.from_rgb(200, 180, 255)
            )
        )

        await hooks.on_ascend(self.bot, ctx.author)

    @commands.command(
        name="snipe",
        help="see the latest message that got deleted",
        usage="!snipe"
    )
    async def snipe(self, ctx):
        message = self.bot.sniped_messages.get(ctx.channel.id)
        if message is None:
            await ctx.send("theres nothing to snipe bro")
            return

        embed = discord.Embed(
            description=message.content,
            color=discord.Color.purple(),
            timestamp=message.created_at
        )
        embed.set_author(
            name=message.author,
            icon_url=message.author.avatar.url if message.author.avatar else None
        )

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        await ctx.send(embed=embed)


    @commands.command(
        name="weather",
        aliases=["w"],
        help="check the weather in a city",
        usage="!weather <city>"
    )
    async def weather(self, ctx: commands.Context, *, city: str):
        city_q = quote_plus(city)

        async with aiohttp.ClientSession() as session:
            geo_url = (
                "https://geocoding-api.open-meteo.com/v1/search"
                f"?name={city_q}&count=1"
            )
            async with session.get(geo_url) as resp:
                geo = await resp.json()

            if not geo.get("results"):
                return await ctx.send("couldn't find that city")

            loc = geo["results"][0]
            lat = loc["latitude"]
            lon = loc["longitude"]
            name = loc["name"]
            country = loc.get("country", "")

            weather_url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
            )
            async with session.get(weather_url) as resp:
                data = await resp.json()

        current = data["current"]

        embed = discord.Embed(
            title=f"🌤️ weather in {name}, {country}",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🌡️ temperature",
            value=f"{current['temperature_2m']}°C",
            inline=True
        )

        embed.add_field(
            name="💧 humidity",
            value=f"{current['relative_humidity_2m']}%",
            inline=True
        )

        embed.add_field(
            name="🌬️ wind",
            value=f"{current['wind_speed_10m']} km/h",
            inline=True
        )

        embed.set_footer(text="data from open-meteo.com")

        await ctx.send(embed=embed)

    @commands.command(name="quote", help="quote a message", usage="(reply) !quote")
    async def quote(self, ctx: commands.Context):
        if not ctx.message.reference:
            return await ctx.send("reply to a message to quote it")

        msg = ctx.message.reference.resolved
        if not isinstance(msg, discord.Message):
            return

        img = render_quote(
            quote=msg.content,
            display_name=msg.author.display_name,
            username=msg.author.name,
            avatar_url=msg.author.display_avatar.url,
            colorful=False
        )

        from io import BytesIO
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        file = discord.File(fp=buffer, filename="quote.png")

        view = QuoteToggleView(
            quote=msg.content,
            display_name=msg.author.display_name,
            username=msg.author.name,
            avatar_url=msg.author.display_avatar.url,
            colorful=False
        )

        await ctx.send(
            file=file,
            view=view
        )

        await hooks.on_quote(self.bot, ctx.author)

    @commands.command(name="setup_parthenon", help="p")
    @commands.has_role(AIRole)
    async def setup_parthenon(self, ctx):
        channel = self.bot.get_channel(DREAMSKY_CHANNEL)

        if not channel:
            return await ctx.send("❌ channel not found")

        self.bot.add_view(ParthenonView(self.bot))

        try:
            created = await setup_parthenon_message(self.bot, channel)

            if created:
                await ctx.send("✅ parthenon gate created")
            else:
                await ctx.send("ℹ️ parthenon gate already exists")

        except Exception as e:
            await ctx.send(f"```py\n{type(e).__name__}: {e}\n```")

TAX_AUDIT_QUESTIONS = [
    ("mc", "what is the standard personal income tax deduction called?",
     {"a": "exemption credit", "b": "standard deduction", "c": "base reduction", "d": "flat allowance"}, "b"),
    ("mc", "which tax is paid on money earned from selling an investment?",
     {"a": "income tax", "b": "sales tax", "c": "capital gains tax", "d": "estate tax"}, "c"),
    ("mc", "a w-2 form reports what?",
     {"a": "business expenses", "b": "wages and taxes withheld by an employer", "c": "investment dividends", "d": "property value"}, "b"),
    ("mc", "what does 'gross income' mean?",
     {"a": "income after all deductions", "b": "total income before deductions", "c": "income from gross sales only", "d": "tax owed"}, "b"),
    ("mc", "what is an irs audit?",
     {"a": "a tax refund", "b": "a review of a taxpayer's accounts and financial information", "c": "a new tax bracket", "d": "a payment plan"}, "b"),
    ("mc", "which of these is a tax advantaged retirement account?",
     {"a": "401(k)", "b": "checking account", "c": "CD", "d": "money market fund"}, "a"),
    ("mc", "what does vat stand for?",
     {"a": "variable asset tax", "b": "value added tax", "c": "verified accounts total", "d": "voluntary asset threshold"}, "b"),
    ("mc", "a tax bracket is based on what?",
     {"a": "total net worth", "b": "age", "c": "taxable income ranges", "d": "number of assets"}, "c"),
    ("mc", "what is tax evasion?",
     {"a": "legally minimizing taxes", "b": "illegally not paying taxes owed", "c": "filing late", "d": "claiming extra deductions"}, "b"),
    ("mc", "a 1099 form is used to report what?",
     {"a": "wages from employment", "b": "income not from an employer, like freelance work", "c": "capital losses", "d": "mortgage interest"}, "b"),
    ("mc", "what does 'progressive tax' mean?",
     {"a": "everyone pays the same rate", "b": "higher incomes pay a higher rate", "c": "tax increases every year", "d": "tax decreases with income"}, "b"),
    ("mc", "what is a tax haven?",
     {"a": "a country with high taxes", "b": "a shelter for refugees", "c": "a place with low or no taxes used to avoid taxation", "d": "a type of savings account"}, "c"),
    ("mc", "what does 'tax incidence' refer to?",
     {"a": "the number of taxes filed", "b": "who ultimately bears the economic burden of a tax", "c": "when taxes are due", "d": "the rate of tax growth"}, "b"),
    ("tf", "a sole proprietor reports business income on their personal tax return.", None, "true"),
    ("tf", "you must pay taxes on illegal income.", None, "true"),
    ("tf", "a tax credit directly reduces the amount of tax you owe, dollar for dollar.", None, "true"),
    ("tf", "a tax deduction reduces taxable income, not tax owed directly.", None, "true"),
    ("tf", "the tax filing deadline is ALWAYS april 30th.", None, "false"),
    ("tf", "depreciation is a non cash deduction businesses can take on assets.", None, "true"),
    ("tf", "payroll taxes fund medicare and social security.", None, "true"),
]

TAX_EXTORTION_EVENTS = [
    {
        "name": "AUDIT",
        "desc": (
            "the tax collector slides a folder across the desk.\n\n"
            "**\"i found an anomaly in your records boy youre so cooked\"**\n\n"
            "bet **{bet}** {quid} that you can call his bluff by typing `bluff`.\n"
            "or pay him **{fee}** {quid} to make it go away by typing `pay`.\n"
            "*8 seconds*"
        ),
        "win_on": "bluff",
        "win_chance": 0.55,
        "fee_ratio": 0.08,
        "bet_ratio": 0.15,
    },
    {
        "name": "EXPENSE",
        "desc": (
            "he squints at a line item in your records.\n\n"
            "**\"this deduction looks VERY suspicious my guy\"**\n\n"
            "defend it by typing `defend` (55% chance) to keep your quid.\n"
            "or concede and pay **{fee}** {quid} by typing `concede`.\n"
            "*8 seconds*"
        ),
        "win_on": "defend",
        "win_chance": 0.55,
        "fee_ratio": 0.10,
        "bet_ratio": 0.0,
    },
    {
        "name": "LOOPHOLE",
        "desc": (
            "you spot a loophole in the tax code.\n\n"
            "**exploit it** by typing `exploit` to bet **{bet}** {quid}.\n"
            "win = keep bet. lose = lose bet AND pay **{fee}** {quid} penalty.\n"
            "or play it safe by typing `skip` to skip this round for free.\n"
            "*8 seconds*"
        ),
        "win_on": "exploit",
        "win_chance": 0.45,
        "fee_ratio": 0.12,
        "bet_ratio": 0.20,
    },
]

async def run_tax_collector_fight(bot, channel, member) -> bool:
    from config import QUID_EMOJI
    from db import db
    from cogs.economy.economycommands import TAX_COLLECTOR_CHANNEL_ID

    if TAX_COLLECTOR_CHANNEL_ID and channel.id != TAX_COLLECTOR_CHANNEL_ID:
        return False

    if channel.id in ACTIVE_TAX_FIGHTS:
            await channel.send(
                "⚠️ An audit is already in progress in this channel! Wait for them to finish.", 
                delete_after=10
            )
            return False
    
    ACTIVE_TAX_FIGHTS.add(channel.id)

    try:
        def check(m):
            return m.author.id == member.id and m.channel == channel

        await channel.send(embed=discord.Embed(
            title="🧾 THE TAX COLLECTOR",
            description=(
                "*a man in a grey suit sits behind a towering pile of ledgers.*\n\n"
                "**\"hohoho you owe me lets see how much\"**\n\n"
                "*type `a` `b` `c` `d` for multiple choice, `true` or `false` for true/false.*"
            ),
            color=discord.Color.from_rgb(60, 60, 60)
        ))
        await asyncio.sleep(3)

        AUDIT_TOTAL   = 10
        AUDIT_NEEDED  = 7
        AUDIT_TIME    = 15

        pool = list(TAX_AUDIT_QUESTIONS)
        random.shuffle(pool)
        selected = pool[:AUDIT_TOTAL]
        correct_count = 0

        for i, (q_type, question, options, answer) in enumerate(selected, 1):
            if q_type == "mc":
                opts_str = "\n".join(f"`{k}` {v}" for k, v in options.items())
                desc = f"*\"{question}\"*\n\n{opts_str}\n\n*{AUDIT_TIME}s*"
            else:
                desc = f"*\"{question}\"*\n\n`true` or `false`\n\n*{AUDIT_TIME}s*"

            remaining_needed = AUDIT_NEEDED - correct_count
            remaining_qs     = AUDIT_TOTAL - i + 1

            await channel.send(embed=discord.Embed(
                title=f"📋 AUDIT - Q{i}/{AUDIT_TOTAL} · {correct_count} correct",
                description=desc,
                color=discord.Color.from_rgb(80, 80, 100)
            ))

            try:
                msg = await bot.wait_for("message", timeout=AUDIT_TIME, check=check)
                pa  = msg.content.lower().strip()
            except asyncio.TimeoutError:
                pa = ""

            if pa == answer:
                correct_count += 1
                await channel.send(embed=discord.Embed(
                    description="✅ correct. your rate drops slightly.",
                    color=discord.Color.green()
                ))
            else:
                suffix = f" {options[answer]}" if q_type == "mc" and options else ""
                await channel.send(embed=discord.Embed(
                    description=f"❌ wrong. answer: `{answer}`{suffix}. your rate rises.",
                    color=discord.Color.red()
                ))

            await asyncio.sleep(0.5)

        tax_rate = 0.40 - max(0, correct_count - 5) * 0.03
        tax_rate = round(max(0.10, min(0.40, tax_rate)), 2)

        await channel.send(embed=discord.Embed(
            description=(
                f"📋 **audit complete.** {correct_count}/{AUDIT_TOTAL} correct.\n"
                f"current tax rate: **{int(tax_rate * 100)}%**"
            ),
            color=discord.Color.from_rgb(80, 80, 100)
        ))
        await asyncio.sleep(2)

        await channel.send(embed=discord.Embed(
            title="💼 PHASE 2",
            description=(
                "*he leans back and lights a cigarette.*\n\n"
                "**\"alright buddy its me you and my severe lung cancer\"**\n\n"
                "three deals."
            ),
            color=discord.Color.from_rgb(60, 40, 20)
        ))
        await asyncio.sleep(2)

        events = random.sample(TAX_EXTORTION_EVENTS, 3)
        event_wins = 0

        for ev in events:
            async with db.pool.acquire() as conn:
                wallet = await conn.fetchval(
                    "SELECT quid FROM economy WHERE user_id=$1", member.id
                ) or 0

            wallet = max(0, wallet)
            fee = max(50, int(wallet * ev["fee_ratio"]))
            bet = max(100, int(wallet * ev["bet_ratio"])) if ev["bet_ratio"] > 0 else 0

            desc = ev["desc"].format(
                bet=f"{bet:,}", fee=f"{fee:,}", quid=QUID_EMOJI
            )

            await channel.send(embed=discord.Embed(
                title=f"📁 {ev['name']}",
                description=desc,
                color=discord.Color.from_rgb(60, 40, 20)
            ))

            try:
                msg = await bot.wait_for("message", timeout=8, check=check)
                choice = msg.content.lower().strip()
            except asyncio.TimeoutError:
                choice = ""

            win_word  = ev["win_on"]
            safe_word = "pay" if win_word == "bluff" else ("concede" if win_word == "defend" else "skip")

            if choice == win_word:
                if random.random() < ev["win_chance"]:
                    event_wins += 1
                    payout = bet if bet > 0 else fee
                    async with db.pool.acquire() as conn:
                        await conn.execute(
                            "UPDATE economy SET quid = quid + $1 WHERE user_id=$2",
                            payout, member.id
                        )
                    await channel.send(embed=discord.Embed(
                        description=f"✅ **success.** +{payout:,} {QUID_EMOJI}",
                        color=discord.Color.green()
                    ))
                else:
                    penalty = fee + (bet if bet > 0 else 0)
                    async with db.pool.acquire() as conn:
                        await conn.execute(
                            "UPDATE economy SET quid = quid - $1 WHERE user_id=$2",
                            penalty, member.id
                        )
                    from cogs.economy.economycommands import update_negative_state
                    await update_negative_state(bot, member.id)
                    await channel.send(embed=discord.Embed(
                        description=f"❌ **failed.** -{penalty:,} {QUID_EMOJI}",
                        color=discord.Color.red()
                    ))
            elif choice == safe_word or choice == "skip":
                if ev["bet_ratio"] == 0:
                    async with db.pool.acquire() as conn:
                        await conn.execute(
                            "UPDATE economy SET quid = quid - $1 WHERE user_id=$2",
                            fee, member.id
                        )
                    from cogs.economy.economycommands import update_negative_state
                    await update_negative_state(bot, member.id)
                    await channel.send(embed=discord.Embed(
                        description=f"💸 paid **{fee:,}** {QUID_EMOJI}. dealt with.",
                        color=discord.Color.orange()
                    ))
                else:
                    await channel.send(embed=discord.Embed(
                        description="⏭️ skipped.",
                        color=discord.Color.greyple()
                    ))
            else:
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE economy SET quid = quid - $1 WHERE user_id=$2",
                        fee, member.id
                    )
                from cogs.economy.economycommands import update_negative_state
                await update_negative_state(bot, member.id)
                await channel.send(embed=discord.Embed(
                    description=f"❓ no response. he takes **{fee:,}** {QUID_EMOJI} anyway.",
                    color=discord.Color.red()
                ))

            await asyncio.sleep(1)

        await channel.send(embed=discord.Embed(
            title="🤝 PHASE 3",
            description=(
                "*he slides a final document toward you.*\n\n"
                "**\"im gonna give you 2 options you either sign or refuse\"**\n\n"
                "your audit score and extortion results determine the outcome.\n\n"
                f"audit: **{correct_count}/{AUDIT_TOTAL}** correct · events won: **{event_wins}/3**\n\n"
                "**refuse** by typing `refuse` to contest his claim and walk free.\n"
                "**sign** by typing `sign` to pay the tax and end it peacefully."
            ),
            color=discord.Color.from_rgb(120, 100, 20)
        ))

        try:
            msg = await bot.wait_for("message", timeout=12, check=check)
            final = msg.content.lower().strip()
        except asyncio.TimeoutError:
            final = "sign"

        fight_won = False

        if final == "refuse":
            if correct_count >= AUDIT_NEEDED or event_wins >= 2:
                fight_won = True
            else:
                fight_won = False
        else:
            async with db.pool.acquire() as conn:
                wallet = await conn.fetchval(
                    "SELECT quid FROM economy WHERE user_id=$1", member.id
                ) or 0
            tax_owed = max(100, int(wallet * tax_rate))
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE economy SET quid = quid - $1 WHERE user_id=$2",
                    tax_owed, member.id
                )
            from cogs.economy.economycommands import update_negative_state
            await update_negative_state(bot, member.id)
            await channel.send(embed=discord.Embed(
                title="🧾 SIGNED",
                description=(
                    f"*you sign the document.*\n\n"
                    f"**{tax_owed:,}** {QUID_EMOJI} paid in taxes.\n"
                    f"*he nods and files it away.*\n\n"
                ),
                color=discord.Color.from_rgb(80, 80, 80)
            ))
            return False

        if fight_won:
            async with db.pool.acquire() as conn:
                wallet = await conn.fetchval(
                    "SELECT quid FROM economy WHERE user_id=$1", member.id
                ) or 0
            refund = max(500, int(wallet * (tax_rate / 2)))
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE economy SET quid = quid + $1 WHERE user_id=$2",
                    refund, member.id
                )
            await channel.send(embed=discord.Embed(
                title="🏆 TAX COLLECTOR DEFEATED",
                description=(
                    f"*he stares at your audit sheet in silence.*\n\n"
                    f"**\"FINE bro ok whatever holy shit calm down\"**\n\n"
                    f"*he writes a refund cheque and slides it across the desk.*\n\n"
                    f"💰 **+{refund:,}** {QUID_EMOJI} refunded.\n"
                ),
                color=discord.Color.gold()
            ))
            return True
        else:
            async with db.pool.acquire() as conn:
                wallet = await conn.fetchval(
                    "SELECT quid FROM economy WHERE user_id=$1", member.id
                ) or 0
            penalty = max(300, int(wallet * (tax_rate + 0.05)))
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE economy SET quid = quid - $1 WHERE user_id=$2",
                    penalty, member.id
                )
            from cogs.economy.economycommands import update_negative_state
            await update_negative_state(bot, member.id)
            await channel.send(embed=discord.Embed(
                title="💀 CASE CLOSED",
                description=(
                    f"*he stamps your file DENIED.*\n\n"
                    f"**\"you should have prepared better lmao watch young sheldon\"**\n\n"
                    f"**{penalty:,}** {QUID_EMOJI} seized as back taxes.\n"
                    f"*the receipt is gone.*"
                ),
                color=discord.Color.dark_red()
            ))
            return False
        
    finally:
        ACTIVE_TAX_FIGHTS.discard(channel.id)

async def setup(bot):
    await bot.add_cog(FunCommands(bot))