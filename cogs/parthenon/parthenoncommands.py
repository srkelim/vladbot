import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime as dt, timezone

from db import db
from config import QUID_EMOJI, PARTHENON_CHANNEL, PARTHENON_ROLE, KEY_CHANNEL, BATTLE_REWARD_QUID, BATTLE_REWARD_XP
from cogs.achievements import hooks
from cogs.fishing.fishingcommands import DODGE_ATTACKS, DODGE_TIME, REEL_NEEDED, REEL_WIND_UP, REEL_ROUNDS, REEL_WINDOW, BAIT_ANSWER_TIME, BAIT_NEEDED, BAIT_QUESTIONS, BAIT_FISH, BAIT_SEQ_LEN, BAIT_SPEED

SCRAMBLE_WORDS = [
    "vladbot","economy","robbery","minneapolis","vacation","achievement",
    "discord","database","currency","marriage","adoption","cooldown",
    "treasure","criminal","puzzle","reaction","pattern","python",
    "channel","server","command","botfight","vacationspot","minigame",
    "cooldowns","leaderboard",
]
MATH_QUESTIONS = [
    ("8 * 7 + 15", "71"), ("24 // 3 + 6 * 5", "38"), ("9 * 9 + 12 * 3", "117"),
    ("15**2 - 200", "25"), ("14 * 4 - 19", "37"), ("18 * 3 + 42", "96"),
    ("45 - 12 * 2", "21"), ("60 // 3 + 17", "37"), ("7 * 11 + 9", "86"),
    ("90 // 5 + 14", "32"), ("16 * 3 - 7", "41"), ("22 + 8 * 6", "70"),
    ("100 // 4 + 36", "61"), ("12 * 8 + 5", "101"), ("17 * 3 + 18", "69"),
]
PATTERN_QUESTIONS = [
    ("2 4 8 16 ?", "32"), ("3 6 9 12 ?", "15"), ("5 10 20 40 ?", "80"),
    ("1 4 9 16 ?", "25"), ("7 14 21 28 ?", "35"), ("10 20 40 80 ?", "160"),
    ("6 12 24 48 ?", "96"), ("9 18 27 36 ?", "45"), ("11 22 44 88 ?", "176"),
    ("4 6 8 10 ?", "12"),
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
    ("what has many teeth but cannot bite", "comb"),
]
MEMORY_SEQUENCES = [
    "🟥🟦🟩🟨","🟨🟥🟦🟩","🟦🟦🟥🟩","🟩🟨🟩🟥",
    "🟥🟩🟨🟦","🟦🟥🟨🟩","🟨🟨🟥🟦","🟩🟥🟦🟨",
]
REVERSE_WORDS = [
    ("TOBDALV","vladbot"),("YMONOCE","economy"),("NOITACAV","vacation"),
    ("EGAIRRAM","marriage"),("NOITPODA","adoption"),("LENNAHC","channel"),
    ("REVRES","server"),("DNAMMOC","command"),("NOITCAER","reaction"),
]
WORD_ELIMINATION = [
    (["apple","banana","carrot","orange"],"carrot"),
    (["dog","cat","lion","car"],"car"),
    (["python","java","banana","c++"],"banana"),
    (["discord","telegram","whatsapp","table"],"table"),
    (["red","blue","green","banana"],"banana"),
    (["gold","silver","bronze","pizza"],"pizza"),
    (["keyboard","mouse","monitor","sandwich"],"sandwich"),
]

def _basic_strategy_hit(player_total, dealer_up, soft):
    if soft:
        if player_total <= 17: return True
        if player_total == 18: return dealer_up in (9, 10, 11)
        return False
    else:
        if player_total <= 11: return True
        if player_total == 12: return dealer_up in (2, 3, 7, 8, 9, 10, 11)
        if player_total <= 16: return dealer_up >= 7
        return False

def _card_val(card):
    r = card[0]
    if r in ("J","Q","K"): return 10
    if r == "A": return 11
    return int(r)

def _hand_total(hand):
    total = sum(_card_val(c) for c in hand)
    aces = sum(1 for c in hand if c[0] == "A")
    while total > 21 and aces:
        total -= 10; aces -= 1
    return total

def _hand_str(hand): return " ".join(f"{r}{s}" for r, s in hand)
def _is_soft(hand):  return sum(_card_val(c) for c in hand) != _hand_total(hand)
def _is_red(card):   return card[1] in ("♥","♦")

def _make_deck():
    suits = ["♠","♥","♦","♣"]
    ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
    deck = [(r,s) for s in suits for r in ranks]
    random.shuffle(deck)
    return deck

async def _boss_vladurk(bot, channel, member) -> bool:
    TOTAL, NEEDED, TL = 20, 16, 8
    def check(m): return m.author.id == member.id and m.channel == channel

    await channel.send(embed=discord.Embed(
        title="🩸 VLADURK",
        description=(
            f"she is faster here.\n\n"
            f"solve **{NEEDED}/{TOTAL}** puzzles. **{TL}s** each.\n"
        ),
        color=discord.Color.dark_red()
    ))
    await asyncio.sleep(2)

    solves = 0
    for i in range(TOTAL):
        ptype = random.choice(["scramble","math","pattern","riddle","reverse","memory","elimination"])

        if ptype == "scramble":
            word = random.choice(SCRAMBLE_WORDS)
            scr  = "".join(random.sample(word, len(word)))
            await channel.send(embed=discord.Embed(description=f"🧩 **unscramble:** `{scr}`", color=discord.Color.blue()))
            answer = word
        elif ptype == "math":
            q, a = random.choice(MATH_QUESTIONS)
            await channel.send(embed=discord.Embed(description=f"🧠 **solve:** `{q}`", color=discord.Color.blue()))
            answer = a
        elif ptype == "pattern":
            q, a = random.choice(PATTERN_QUESTIONS)
            await channel.send(embed=discord.Embed(description=f"🔢 **complete:** `{q}`", color=discord.Color.blue()))
            answer = a
        elif ptype == "riddle":
            q, a = random.choice(RIDDLES)
            await channel.send(embed=discord.Embed(description=f"❓ **riddle:** {q}", color=discord.Color.blue()))
            answer = a
        elif ptype == "reverse":
            q, a = random.choice(REVERSE_WORDS)
            await channel.send(embed=discord.Embed(description=f"🔁 **reverse:** `{q}`", color=discord.Color.blue()))
            answer = a
        elif ptype == "memory":
            seq  = random.choice(MEMORY_SEQUENCES)
            e2w  = {"🟥":"red","🟦":"blue","🟩":"green","🟨":"yellow"}
            emb  = discord.Embed(description="🧠 **memorize...**", color=discord.Color.blue())
            msg  = await channel.send(embed=emb)
            for j, em in enumerate(seq, 1):
                emb.description = f"🧠 **{j}** - {em}"
                await msg.edit(embed=emb)
                await asyncio.sleep(1)
            await asyncio.sleep(1)
            emb.description = "🧠 **type the colors in order** ex. `red blue green yellow`"
            await msg.edit(embed=emb)
            answer = " ".join(e2w[e] for e in seq)
        else:
            opts, a = random.choice(WORD_ELIMINATION)
            await channel.send(embed=discord.Embed(description=f"❌ **which doesnt belong?** {', '.join(opts)}", color=discord.Color.blue()))
            answer = a

        remaining = TOTAL - i - 1
        if (NEEDED - solves) > remaining + 1:
            await channel.send(embed=discord.Embed(
                title="💀 vladurk wins",
                description=f"**{member.display_name}** can no longer reach {NEEDED}. `{solves}/{TOTAL}`",
                color=discord.Color.dark_red()
            ))
            return False

        try:
            msg = await bot.wait_for("message", timeout=TL, check=check)
            if msg.content.lower().strip() == answer.lower():
                solves += 1
                await channel.send(embed=discord.Embed(description=f"✅ correct! `{solves}/{NEEDED}`", color=discord.Color.green()))
            else:
                await channel.send(embed=discord.Embed(description=f"❌ wrong. answer: **{answer}**", color=discord.Color.red()))
        except asyncio.TimeoutError:
            await channel.send(embed=discord.Embed(description=f"⏰ times up. answer: **{answer}**", color=discord.Color.red()))

    if solves >= NEEDED:
        await channel.send(embed=discord.Embed(
            title="🏆 VLADURK FALLS",
            description=f"**{member.display_name}** solved `{solves}/{TOTAL}`. she crumbles.",
            color=discord.Color.gold()
        ))
        return True
    else:
        await channel.send(embed=discord.Embed(
            title="💀 VLADURK WINS",
            description=f"**{member.display_name}** - `{solves}/{TOTAL}`. not enough.",
            color=discord.Color.dark_red()
        ))
        return False

async def _boss_sigshark(bot, channel, member) -> bool:
    async def phase_dodge(bot, channel, member) -> bool:
        attacks = list(DODGE_ATTACKS.items())
        random.shuffle(attacks)
        selected = attacks[:5]

        await channel.send(embed=discord.Embed(
            title="phase 1 - dodge",
            description=(
                "the sigshark is attacking!\n\n"
                "**respond with the correct dodge:**\n"
                "`left` `right` `dive` `jump`\n\n"
                f"*{DODGE_TIME} seconds per attack. one wrong move and you're done*"
            ),
            color=discord.Color.from_rgb(30, 10, 40),
        ))
        await asyncio.sleep(2)

        def check(m):
            return m.author.id == member.id and m.channel == channel

        for i, (attack, counter) in enumerate(selected, 1):
            await channel.send(embed=discord.Embed(
                title=f"💥 ATTACK {i}/5",
                description=f"**{attack}**\n\nwhat do you do?",
                color=discord.Color.red(),
            ))

            try:
                msg = await bot.wait_for("message", timeout=DODGE_TIME, check=check)
                response = msg.content.lower().strip()
            except asyncio.TimeoutError:
                await channel.send(embed=discord.Embed(
                    description=f"⏰ too slow! the correct dodge was **{counter}**.\nthe shark tears through you.",
                    color=discord.Color.dark_red(),
                ))
                return False

            if response == counter:
                await channel.send(embed=discord.Embed(
                    description=f"✅ **{counter.upper()}!** you dodge the attack!",
                    color=discord.Color.green(),
                ))
            else:
                await channel.send(embed=discord.Embed(
                    description=f"❌ wrong! you needed **{counter}**, not `{response}`.\nthe shark catches you.",
                    color=discord.Color.dark_red(),
                ))
                return False

            await asyncio.sleep(0.6)

        return True


    async def phase_reel(bot, channel, member) -> bool:
        await channel.send(embed=discord.Embed(
            title="phase 2 - strike the shark yo",
            description=(
                "the shark is circling...\n\n"
                "when **STRIKE 🎣** appears, click it immediately.\n"
                f"*you have {REEL_WINDOW}s. miss {REEL_ROUNDS - REEL_NEEDED + 1} and it's over.*"
            ),
            color=discord.Color.from_rgb(30, 10, 40),
        ))
        await asyncio.sleep(2)

        hits = 0
        misses = 0
        max_misses = REEL_ROUNDS - REEL_NEEDED

        for round_num in range(1, REEL_ROUNDS + 1):
            wind_up = random.uniform(*REEL_WIND_UP)
            steps = int(wind_up / 0.6)

            embed = discord.Embed(
                title=f"🦈 ROUND {round_num}/{REEL_ROUNDS}  |  hits: {hits}  misses: {misses}",
                description="🌊 *the shark is circling...*",
                color=discord.Color.blurple(),
            )
            msg = await channel.send(embed=embed)

            for _ in range(steps):
                await asyncio.sleep(0.6)

            struck = False
            strike_event = asyncio.Event()

            class StrikeView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=REEL_WINDOW)

                @discord.ui.button(label="STRIKE 🎣", style=discord.ButtonStyle.success)
                async def strike(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != member.id:
                        return await interaction.response.send_message("not your fight", ephemeral=True)
                    nonlocal struck
                    struck = True
                    strike_event.set()
                    self.stop()
                    await interaction.response.defer()

                async def on_timeout(self):
                    strike_event.set()

            view = StrikeView()
            embed.description = "🎣 **STRIKE NOW!!**"
            embed.color = discord.Color.green()
            await msg.edit(embed=embed, view=view)

            await strike_event.wait()

            for item in view.children:
                item.disabled = True
            await msg.edit(view=view)

            if struck:
                hits += 1
                await channel.send(embed=discord.Embed(
                    description=f"✅ **STRIKE!** ({hits}/{REEL_ROUNDS})",
                    color=discord.Color.green(),
                ))
            else:
                misses += 1
                await channel.send(embed=discord.Embed(
                    description=f"❌ missed the window! ({misses} miss{'es' if misses > 1 else ''})",
                    color=discord.Color.red(),
                ))
                if misses > max_misses:
                    await channel.send(embed=discord.Embed(
                        description="the shark dives. you lost the window.",
                        color=discord.Color.dark_red(),
                    ))
                    return False

            await asyncio.sleep(0.8)

        return hits >= REEL_NEEDED


    async def phase_strike(bot, channel, member) -> bool:
        await channel.send(embed=discord.Embed(
            title="phase 3 - amazing memory",
            description=(
                "a school of fish is swimming past...\n\n"
                "**watch carefully.** you'll be asked questions about what you saw.\n"
                f"*need {BAIT_NEEDED}/{BAIT_QUESTIONS} correct*"
            ),
            color=discord.Color.from_rgb(30, 10, 40),
        ))
        await asyncio.sleep(2)

        sequence = [random.choice(BAIT_FISH) for _ in range(BAIT_SEQ_LEN)]

        embed = discord.Embed(
            title="🌊 watch the water...",
            description="...",
            color=discord.Color.blurple(),
        )
        msg = await channel.send(embed=embed)

        for i, fish in enumerate(sequence, 1):
            embed.description = f"**{i}/{BAIT_SEQ_LEN}** - {fish}"
            await msg.edit(embed=embed)
            await asyncio.sleep(BAIT_SPEED)

        embed.description = "🌊 *they're gone. answer quickly.*"
        await msg.edit(embed=embed)
        await asyncio.sleep(0.8)

        def make_questions(seq):
            pool = []

            counts = {}
            for f in seq:
                counts[f] = counts.get(f, 0) + 1
            target = random.choice(list(counts.keys()))
            pool.append((
                f"how many **{target}** swam past?",
                str(counts[target])
            ))

            pos = random.randint(1, len(seq))
            pool.append((
                f"what was the **{pos}{'st' if pos==1 else 'nd' if pos==2 else 'rd' if pos==3 else 'th'}** fish?",
                seq[pos - 1]
            ))

            unique = list(set(seq))
            if len(unique) >= 2:
                a, b = random.sample(unique, 2)
                idx_a = seq.index(a)
                idx_b = seq.index(b)
                answer = "yes" if idx_a < idx_b else "no"
                pool.append((
                    f"did **{a}** appear before **{b}**? (`yes` / `no`)",
                    answer
                ))
            else:
                pool.append((
                    "what was the **last** fish?",
                    seq[-1]
                ))

            random.shuffle(pool)
            return pool[:BAIT_QUESTIONS]

        questions = make_questions(sequence)

        EMOJI_TO_NAME = {
            "🐟": "fish",
            "🦈": "shark",
            "🐡": "blowfish",
            "🐙": "octopus",
            "🐠": "tropical fish",
            "🦑": "squid",
            "🐬": "dolphin",
            "🦐": "shrimp",
        }
        NAME_TO_EMOJI = {v: k for k, v in EMOJI_TO_NAME.items()}

        def answers_match(given: str, answer: str) -> bool:
            given = given.strip().lower()
            answer_lower = answer.strip().lower()
            if given == answer_lower:
                return True
            if answer in EMOJI_TO_NAME:
                return given == EMOJI_TO_NAME[answer].lower()
            if answer_lower in NAME_TO_EMOJI:
                return given == NAME_TO_EMOJI[answer_lower]
            return False

        def check(m):
            return m.author.id == member.id and m.channel == channel

        correct = 0
        for i, (question, answer) in enumerate(questions, 1):
            hint = ""
            if answer in EMOJI_TO_NAME:
                hint = f"\n*(you can answer with the emoji or its name: **{EMOJI_TO_NAME[answer]}**)*"

            await channel.send(embed=discord.Embed(
                title=f"❓ QUESTION {i}/{BAIT_QUESTIONS}  |  {correct} correct",
                description=question + hint,
                color=discord.Color.orange(),
            ))

            try:
                msg = await bot.wait_for("message", timeout=BAIT_ANSWER_TIME, check=check)
                given = msg.content.strip().lower()
                if answers_match(given, answer):
                    correct += 1
                    await channel.send(embed=discord.Embed(
                        description="✅ correct!",
                        color=discord.Color.green(),
                    ))
                else:
                    display = f"{answer} ({EMOJI_TO_NAME[answer]})" if answer in EMOJI_TO_NAME else answer
                    await channel.send(embed=discord.Embed(
                        description=f"❌ wrong!! answer was **{display}**",
                        color=discord.Color.red(),
                    ))
            except asyncio.TimeoutError:
                display = f"{answer} ({EMOJI_TO_NAME[answer]})" if answer in EMOJI_TO_NAME else answer
                await channel.send(embed=discord.Embed(
                    description=f"⏰ time's up!! answer was **{display}**",
                    color=discord.Color.red(),
                ))

            await asyncio.sleep(0.4)

        if correct >= BAIT_NEEDED:
            return True

        await channel.send(embed=discord.Embed(
            description=f"❌ {correct}/{BAIT_QUESTIONS}. not enough. the shark slips away.",
            color=discord.Color.dark_red(),
        ))
        return False

    if not await phase_dodge(bot, channel, member):
        return False

    if not await phase_reel(bot, channel, member):
        return False

    if not await phase_strike(bot, channel, member):
        return False

    return True

async def _boss_dealer(bot, channel, member) -> bool:
    from cogs.fun.funcommands import run_dealer_escape
    return await run_dealer_escape(bot, channel, member)

async def _boss_yeti(bot, channel, member) -> bool:
    from cogs.fun.funcommands import run_yeti_fight
    return await run_yeti_fight(bot, channel, member)

async def _boss_socrates(bot, channel, member) -> bool:
    from cogs.fun.funcommands import SOCRATES_QUESTIONS
    TOTAL, NEEDED, TL = 30, 26, 15
    def check(m): return m.author.id == member.id and m.channel == channel

    await channel.send(embed=discord.Embed(
        title="🏛️ SOCRATES",
        description=(
            f"he is sharper here.\n\n"
            f"**{NEEDED}/{TOTAL}** correct. **{TL}s** each.\n"
            "mc: `a b c d` - true/false: `true` or `false`"
        ),
        color=discord.Color.from_rgb(180, 150, 80)
    ))
    await asyncio.sleep(2)

    pool = list(SOCRATES_QUESTIONS)
    random.shuffle(pool)
    selected = pool[:TOTAL]
    correct = 0

    for i, (qt, question, options, answer) in enumerate(selected, 1):
        if (NEEDED - correct) > (TOTAL - i + 1):
            await channel.send(embed=discord.Embed(
                title="🏛️ SOCRATES WINS",
                description=f"**{member.display_name}** can no longer reach {NEEDED}. `{correct}/{TOTAL}`",
                color=discord.Color.dark_red()
            ))
            return False

        if qt == "mc":
            desc = f"*\"{question}\"*\n\n" + "\n".join(f"`{k}` {v}" for k, v in options.items()) + f"\n\n*{TL}s*"
        else:
            desc = f"*\"{question}\"*\n\n`true` or `false`\n\n*{TL}s*"

        await channel.send(embed=discord.Embed(
            title=f"🏛️ Q {i}/{TOTAL}  -  {correct} correct",
            description=desc,
            color=discord.Color.from_rgb(180, 150, 80)
        ))
        try:
            msg = await bot.wait_for("message", timeout=TL, check=check)
            pa  = msg.content.lower().strip()
        except asyncio.TimeoutError:
            pa = ""

        if pa == answer:
            correct += 1
            await channel.send(embed=discord.Embed(description="✅ correct.", color=discord.Color.green()))
        else:
            suffix = f" {options[answer]}" if qt == "mc" else ""
            await channel.send(embed=discord.Embed(
                description=f"❌ wrong. answer: `{answer}`{suffix}.", color=discord.Color.red()
            ))
        await asyncio.sleep(0.5)

    if correct >= NEEDED:
        await channel.send(embed=discord.Embed(
            title="🏛️ SOCRATES YIELDS",
            description=f"**{member.display_name}** answered {correct}/{TOTAL}.\n*\"impressive, for a mortal.\"*",
            color=discord.Color.gold()
        ))
        return True
    else:
        await channel.send(embed=discord.Embed(
            title="🏛️ SOCRATES WINS",
            description=f"**{member.display_name}** answered {correct}/{TOTAL}. needed {NEEDED}.",
            color=discord.Color.dark_red()
        ))
        return False

async def _boss_aphrodite(bot, channel, member) -> bool:
    from cogs.hell.hellcommands import run_aphrodite
    return await run_aphrodite(bot, channel, member)

async def _boss_anti_vlad(bot, channel, member) -> tuple[bool, str]:
    """Returns (success, outcome) where outcome is 'won' | 'joined' | 'failed'."""
    from cogs.hell.hellcommands import run_anti_vlad
    result = await run_anti_vlad(bot, channel, member)
    if result == "won":    return True, "won"
    if result == "joined": return True, "joined"
    return False, "failed"

async def _boss_king_minnea(bot, channel, member) -> bool:
    from cogs.hell.hellcommands import run_king_minnea
    return await run_king_minnea(bot, channel, member)

async def _boss_caligula(bot, channel, member) -> bool:
    from cogs.hell.hellcommands import run_caligula
    return await run_caligula(bot, channel, member)

async def _boss_genghis_khan(bot, channel, member) -> bool:
    from cogs.hell.hellcommands import run_genghis_khan
    return await run_genghis_khan(bot, channel, member)

async def _boss_dealer_sr(bot, channel, member) -> bool:
    from cogs.hell.hellcommands import run_dealer_sr
    return await run_dealer_sr(bot, channel, member)

async def _boss_socrates_prime(bot, channel, member) -> bool:
    from cogs.fun.funcommands import run_socrates_prime
    return await run_socrates_prime(bot, channel, member)

class BattleStartView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=30)
        self.member    = member
        self.confirmed = False

    @discord.ui.button(label="enter the parthenon", style=discord.ButtonStyle.danger)
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            return await interaction.response.send_message("this isnt yours lil bro", ephemeral=True)
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="turn back", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            return await interaction.response.send_message("this isnt yours lil bro", ephemeral=True)
        self.stop()
        await interaction.response.edit_message(
            content="you step away from the gates", embed=None, view=None
        )

BOSS_ROSTER = [
    ("vladurk", "🩸 VLADURK",  _boss_vladurk),
    ("sigshark", "🦈 SUPREME SIGSHARK", _boss_sigshark),
    ("dealer", "🃏 THE DEALER", _boss_dealer),
    ("yeti", "🦣 THE YETI", _boss_yeti),
    ("socrates", "🏛️ SOCRATES", _boss_socrates),
    ("aphrodite", "❤️‍🔥 APHRODITE", _boss_aphrodite),
    ("anti_vlad", "🗡️ THE ANTI-VLAD", None),
    ("king_minnea", "👑 KING MINNEA", _boss_king_minnea),
    ("caligula", "🐐 CALIGULA", _boss_caligula),
    ("genghis_khan", "⚡ GENGHIS KHAN", _boss_genghis_khan),
    ("dealer_sr", "🎴 DEALER SR.", _boss_dealer_sr),
    ("socrates_prime", "👁️ SOCRATES PRIME", _boss_socrates_prime),
]

async def _run_gauntlet(bot, channel, member) -> tuple[bool, str | None]:
    """
    Runs all 12 bosses in sequence.
    Returns (cleared: bool, anti_vlad_outcome: 'won'|'joined'|None).
    """
    anti_vlad_outcome = None

    for idx, (boss_id, boss_name, fight_fn) in enumerate(BOSS_ROSTER, 1):
        remaining_after = len(BOSS_ROSTER) - idx
        await asyncio.sleep(1.5)
        await channel.send(embed=discord.Embed(
            title=f"⚡ BOSS {idx}/12 - {boss_name}",
            description=(
                f"*{remaining_after} boss{'es' if remaining_after != 1 else ''} remain after this.*"
                if remaining_after > 0 else "*the final trial.*"
            ),
            color=discord.Color.dark_red()
        ))
        await asyncio.sleep(2)

        if boss_id == "anti_vlad":
            success, outcome = await _boss_anti_vlad(bot, channel, member)
            anti_vlad_outcome = outcome
            if not success:
                return False, None
            if outcome == "joined":
                await channel.send(embed=discord.Embed(
                    description=(
                        "*you took his hand.*\n"
                    ),
                    color=discord.Color.from_rgb(0, 0, 0)
                ))
            else:
                await channel.send(embed=discord.Embed(
                    description="*he yields. the gates ahead crack open.*",
                    color=discord.Color.gold()
                ))
            continue

        result = await fight_fn(bot, channel, member)

        if not result:
            await channel.send(embed=discord.Embed(
                title="GAUNTLET OVER",
                description=(
                    f"**{member.display_name}** fell at **{boss_name}**.\n\n"
                    "*the parthenon closes.*"
                ),
                color=discord.Color.dark_red()
            ))
            return False, None

        if idx < len(BOSS_ROSTER):
            await channel.send(embed=discord.Embed(
                description=f"✅ **{boss_name}** defeated. catch your breath...",
                color=discord.Color.green()
            ))

    return True, anti_vlad_outcome

class ParthenonCommands(commands.Cog):

    def __init__(self, bot: discord.Client):
        self.bot = bot

    @commands.command(name="battle", help="enter the parthenon gauntlet", usage="!battle")
    async def battle(self, ctx: commands.Context):

        if ctx.channel.id != PARTHENON_CHANNEL:
            return await ctx.send("`!battle` can only be used inside the parthenon.")

        embed = discord.Embed(
            title="THE PARTHENON",
            description=(
                f"**{ctx.author.display_name}** stands before the gates.\n\n"
                "12 bosses await.\n"
            ),
            color=discord.Color.gold()
        )

        view = BattleStartView(ctx.author)
        msg = await ctx.send(embed=embed, view=view)
        await view.wait()

        if not view.confirmed:
            await msg.edit(content="you step away from the gates.", embed=None, view=None)
            return

        await msg.edit(
            embed=discord.Embed(
                title="⚡ THE GATES OPEN",
                description=(
                    "*twelve gods awaken.*\n\n"
                ),
                color=discord.Color.gold()
            ),
            view=None
        )

        await asyncio.sleep(3)

        cleared, anti_vlad_outcome = await _run_gauntlet(
            self.bot,
            ctx.channel,
            ctx.author
        )

        if not cleared:
            return

        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE economy SET quid = quid + $1 WHERE user_id = $2",
                BATTLE_REWARD_QUID,
                ctx.author.id
            )

            await conn.execute(
                """
                INSERT INTO xp (user_id, xp)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET xp = xp.xp + $2
                """,
                ctx.author.id,
                BATTLE_REWARD_XP
            )

        await ctx.send(embed=discord.Embed(
            title="👑 THE PARTHENON FALLS",
            description=(
                f"**{ctx.author.mention}** defeated all 12 gods.\n\n"
                f"**+{BATTLE_REWARD_QUID:,}** {QUID_EMOJI}\n"
                f"**+{BATTLE_REWARD_XP:,} XP**\n\n"
            ),
            color=discord.Color.gold()
        ))

        await hooks.parthenon(self.bot, ctx.author)

async def setup(bot):
    await bot.add_cog(ParthenonCommands(bot))