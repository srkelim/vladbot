import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime as dt, timezone, timedelta

from db import db
from config import QUID_EMOJI, EVIL_EMOJI
from cogs.achievements import hooks
from cogs.fishing.fishingcommands import HELL_LAYERS, HELL_CHANNEL_IDS, get_hell_layer, get_hell_layer_by_name, HELL_HELLEVATOR_ROLE

def mode_hint(mode):
    return {
        "NORMAL": "the judge speaks plainly.",
        "INVERTED": "the judge contradicts itself.",
        "SILENCE": "the judge accepts no speech.",
    }[mode]

class CaligulaState:
    def __init__(self):
        self.mode = "NORMAL"
        self.history = []

    def update_mode(self):
        if len(self.history) >= 6:
            self.mode = random.choice(["INVERTED", "NORMAL", "SILENCE"])

    def evaluate(self, choice, truth):
        if self.mode == "NORMAL":
            return choice == ("accept" if truth else "reject")

        if self.mode == "INVERTED":
            return choice != ("accept" if truth else "reject")

        if self.mode == "SILENCE":
            return choice is None

class CaligulaView(discord.ui.View):
    def __init__(self, state, truth):
        super().__init__(timeout=5)
        self.state = state
        self.truth = truth
        self.choice = None
        self.result = None

    async def press(self, interaction, value):
        self.choice = value
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="JUDGE", style=discord.ButtonStyle.primary)
    async def accept(self, interaction, button):
        await self.press(interaction, "accept")

    @discord.ui.button(label="DENY", style=discord.ButtonStyle.danger)
    async def reject(self, interaction, button):
        await self.press(interaction, "reject")

    @discord.ui.button(label="SILENCE", style=discord.ButtonStyle.secondary)
    async def nothing(self, interaction, button):
        await self.press(interaction, None)

async def get_evil_quid(user_id: int) -> int:
    async with db.pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT amount FROM evil_quid WHERE user_id=$1", user_id
        ) or 0

async def add_evil_quid(user_id: int, amount: int):
    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO evil_quid (user_id, amount)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET amount = evil_quid.amount + $2
            """,
            user_id, amount
        )

async def spend_evil_quid(user_id: int, amount: int) -> bool:
    async with db.pool.acquire() as conn:
        current = await conn.fetchval("SELECT amount FROM evil_quid WHERE user_id=$1", user_id) or 0
        if current < amount:
            return False
        await conn.execute(
            "UPDATE evil_quid SET amount = amount - $1 WHERE user_id=$2",
            amount, user_id
        )
        return True

async def has_cleared_layer(user_id: int, layer_name: str) -> bool:
    async with db.pool.acquire() as conn:
        return bool(await conn.fetchval(
            "SELECT 1 FROM hell_progress WHERE user_id=$1 AND layer_name=$2",
            user_id, layer_name
        ))

async def mark_layer_cleared(user_id: int, layer_name: str):
    async with db.pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO hell_progress (user_id, layer_name, cleared_at) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
            user_id, layer_name, dt.now(timezone.utc)
        )

async def get_current_layer_num(member: discord.Member) -> int | None:
    role_ids = {r.id for r in member.roles}
    for layer in reversed(HELL_LAYERS):
        if layer["role"] in role_ids:
            return layer["layer_num"]
    return None

async def get_cleared_count(user_id: int) -> int:
    async with db.pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM hell_progress WHERE user_id=$1", user_id) or 0

async def run_aphrodite(bot, channel, member) -> bool:
    def check(m):
        return m.author.id == member.id and m.channel == channel

    COMMANDS = ["resist", "deny", "ignore", "look away"]

    TEMPTATIONS = [
        {
            "text": "💋 *\"stay with me.\"*",
            "rule": "resist",
            "time": 5
        },
        {
            "text": "🌹 the scent reminds you of your childhood.",
            "rule": "deny",
            "time": 5
        },
        {
            "text": "✨ *\"you will never be lonely again.\"*",
            "rule": "ignore",
            "time": 5
        },
        {
            "text": "❤️‍🔥 you see your perfect future.",
            "rule": "look away",
            "time": 3
        },
        {
            "text": "💎 wealth, power, admiration.",
            "rule": "resist",
            "time": 5
        },
        {
            "text": "🪞 someone you lost reaches out to you.",
            "rule": "deny",
            "time": 3
        },
        {
            "text": "👁️ *\"just stop fighting.\"*",
            "rule": "look away",
            "time": 4
        },
    ]

    await channel.send(embed=discord.Embed(
        title="❤️ APHRODITE",
        description=(
            f"**{member.display_name}**, aphrodite tests your will.\n\n"
            "respond correctly to each temptation.\n"
            "commands may vary: `resist`, `deny`, `ignore`, `look away`\n\n"
        ),
        color=discord.Color.from_rgb(220, 80, 120)
    ))

    await asyncio.sleep(2)

    last_inputs = []

    for i, t in enumerate(TEMPTATIONS, 1):
        fake_hint = random.choice(COMMANDS)
        use_fake = random.random() < 0.4

        hint_text = f"*type `{fake_hint}`*" if use_fake else "*choose wisely.*"

        await channel.send(embed=discord.Embed(
            description=f"**temptation {i}/7**\n\n{t['text']}\n\n{hint_text}",
            color=discord.Color.from_rgb(220, 80, 120)
        ))

        try:
            msg = await bot.wait_for("message", timeout=t["time"], check=check)
            answer = msg.content.lower().strip()

            last_inputs.append(answer)
            if len(last_inputs) >= 3 and len(set(last_inputs[-3:])) == 1:
                await channel.send(embed=discord.Embed(
                    description="💔 **you acted without thinking.** she saw through you.",
                    color=discord.Color.red()
                ))
                return False

            if answer == t["rule"]:
                await channel.send(embed=discord.Embed(
                    description="✅ resisted.",
                    color=discord.Color.green()
                ))
            else:
                await channel.send(embed=discord.Embed(
                    description=f"💔 **wrong choice.** she smiles knowingly.",
                    color=discord.Color.red()
                ))
                return False

        except asyncio.TimeoutError:
            await channel.send(embed=discord.Embed(
                description="⏰ **hesitation is surrender.**",
                color=discord.Color.red()
            ))
            return False

        await asyncio.sleep(0.5)

    await channel.send(embed=discord.Embed(
        description="✨ **she steps aside.** *\"impressive... you truly see.\"*",
        color=discord.Color.gold()
    ))

    return True

async def run_genghis_khan(bot, channel, member) -> bool:
    def check(m):
        return m.author.id == member.id and m.channel == channel

    TACTICS = {
        "🏹 ARROW RAIN":     "shield",
        "🐎 CAVALRY CHARGE": "scatter",
        "🔥 FIRE SIEGE":     "water",
        "⚔️ FLANKING":       "hold",
        "🌪️ FEIGNED RETREAT":"advance",
        "🗡️ PINCER MOVE":    "break",
        "🏔️ HIGH GROUND":    "flank",
    }

    FAKE_TACTICS = {
        "🌑 SHADOW CHARGE": "ignore",
        "🩸 BLOOD RUSH":    "ignore",
    }

    COMMANDS = list(set(TACTICS.values()) | {"ignore"})

    await channel.send(embed=discord.Embed(
        title="⚡ GENGHIS KHAN",
        description=(
            f"the great khan rides towards you.\n\n"
            "commands: `shield, scatter, water, hold, advance, break, flank, ignore`"
        ),
        color=discord.Color.from_rgb(180, 80, 0)
    ))

    await asyncio.sleep(2)

    await channel.send(embed=discord.Embed(
        title="PHASE 1",
        color=discord.Color.from_rgb(180, 80, 0)
    ))

    for tactic, counter in random.sample(list(TACTICS.items()), 5):
        shown = tactic

        invert = random.random() < 0.25
        hint = "⚠️ he anticipates you. do it twice." if invert else ""

        await channel.send(embed=discord.Embed(
            description=f"`{shown}`\n{hint}",
            color=discord.Color.from_rgb(180, 80, 0)
        ))

        try:
            msg = await bot.wait_for("message", timeout=6, check=check)
            ans = msg.content.lower().strip()

            if invert:
                if ans == counter:
                    raise ValueError("predicted")
            else:
                if ans != counter:
                    raise ValueError("wrong")

            await channel.send("✅")

        except:
            await channel.send(embed=discord.Embed(
                description=f"💀 failed. correct: `{counter}`",
                color=discord.Color.dark_red()
            ))
            return False

        await asyncio.sleep(0.4)

    await channel.send("✅ **phase 1 cleared.**")
    await asyncio.sleep(1.5)

    await channel.send(embed=discord.Embed(
        title="PHASE 2",
        description="respond with BOTH counters in ONE message (ex. `shield scatter`)",
        color=discord.Color.from_rgb(180, 80, 0)
    ))

    pool = list(TACTICS.items())
    sample_size = len(pool) - (len(pool) % 2)

    pairs = random.sample(pool, sample_size)
    pair_chunks = list(zip(pairs[::2], pairs[1::2]))

    for (t1, c1), (t2, c2) in pair_chunks:

        shown1 = t1
        shown2 = t2

        await channel.send(embed=discord.Embed(
            description=f"`{shown1}` + `{shown2}`",
            color=discord.Color.from_rgb(180, 80, 0)
        ))

        try:
            msg = await bot.wait_for("message", timeout=6, check=check)
            answers = msg.content.lower().split()

            if set(answers) == {c1, c2}:
                await channel.send("✅")
            else:
                raise ValueError()

        except:
            await channel.send(embed=discord.Embed(
                description=f"💀 failed. correct: `{c1} {c2}`",
                color=discord.Color.dark_red()
            ))
            return False

        await asyncio.sleep(0.4)

    await channel.send("✅ **phase 2 cleared.**")
    await asyncio.sleep(1.5)

    await channel.send(embed=discord.Embed(
        title="⚡ PHASE 3",
        color=discord.Color.dark_red()
    ))

    pool = list(TACTICS.items()) + list(FAKE_TACTICS.items())

    for _ in range(3):
        tactic, counter = random.choice(pool)

        invert = random.random() < 0.3

        await channel.send(embed=discord.Embed(
            description=f"⚡ `{tactic}`",
            color=discord.Color.dark_red()
        ))

        try:
            msg = await bot.wait_for("message", timeout=3, check=check)
            ans = msg.content.lower().strip()

            if invert:
                if ans == counter:
                    raise ValueError()
            else:
                if ans != counter:
                    raise ValueError()

            await channel.send("✅")

        except:
            await channel.send(embed=discord.Embed(
                description=f"💀 the khan overwhelms you.",
                color=discord.Color.dark_red()
            ))
            return False

        await asyncio.sleep(0.25)

    await channel.send(embed=discord.Embed(
        description="🏆 **the khan yields.**",
        color=discord.Color.gold()
    ))

    return True


async def run_caligula(bot, channel, member) -> bool:
    def check(m):
        return m.author.id == member.id and m.channel == channel

    STATEMENTS = [
        ("the sun is made of fire", True),
        ("you are not real", False),
        ("caligula is sane", False),
        ("water is wet", True),
        ("truth is optional", False),
        ("you must obey", False),
        ("silence is safety", True),
    ]

    state = CaligulaState()

    await channel.send(
        embed=discord.Embed(
            title="🐐 CALIGULA",
            description=(
                f"**{member.display_name}**\n\n"
                "caligula does not ask questions.\n"
            ),
            color=discord.Color.purple()
        )
    )

    await asyncio.sleep(3)

    for i in range(10):
        statement, truth = random.choice(STATEMENTS)

        state.update_mode()

        view = CaligulaView(state, truth)

        msg = await channel.send(
            embed=discord.Embed(
                title=f"DECREE {i+1}",
                description=statement,
                color=discord.Color.dark_purple()
            ).set_footer(text=mode_hint(state.mode)),
            view=view
        )

        await view.wait()

        state.history.append(view.choice)

        if not state.evaluate(view.choice, truth):
            await msg.edit(view=None)
            await channel.send("💀 *he laughs maniacally.*")
            return False

        await msg.edit(view=None)
        await channel.send("✅")

        await asyncio.sleep(0.6)

    await channel.send(
        embed=discord.Embed(
            description="👑 *caligula stops speaking.*",
            color=discord.Color.gold()
        )
    )

    return True

async def run_king_minnea(bot, channel, member) -> bool:
    def check(m):
        return m.author.id == member.id and m.channel == channel

    await channel.send(embed=discord.Embed(
        title="🩸 KING MINNEA",
        description=(
            f"the pillager king stands before you.\n\n"
        ),
        color=discord.Color.dark_red()
    ))

    await asyncio.sleep(2)

    RESOURCES = ["grain", "gold", "water", "steel", "wood"]

    def get_rule():
        return random.choice(["normal", "reverse", "double"])

    await channel.send(embed=discord.Embed(
        title="🩸 PHASE 1",
        color=discord.Color.dark_red()
    ))

    rule = "normal"

    for i in range(5):
        resource = random.choice(RESOURCES)

        if random.random() < 0.25:
            rule = get_rule()

        if rule == "normal":
            expected = resource
            prompt = f"⚔️ pillagers attack **{resource}**"

        elif rule == "reverse":
            expected != resource
            prompt = f"⚔️ pillagers avoid **{resource}**"

        elif rule == "double":
            expected = resource + " " + resource
            prompt = f"⚔️ heavy assault on **{resource}** (respond twice)"

        await channel.send(embed=discord.Embed(
            description=prompt,
            color=discord.Color.dark_red()
        ))

        try:
            msg = await bot.wait_for("message", timeout=6, check=check)
            ans = msg.content.lower().strip()

            if rule == "normal":
                if ans != resource:
                    raise ValueError()

            elif rule == "reverse":
                if ans == resource:
                    raise ValueError()

            elif rule == "double":
                if ans != f"{resource} {resource}":
                    raise ValueError()

            await channel.send("✅")

        except:
            await channel.send("💀 the siege breaks your defenses.")
            return False

        await asyncio.sleep(0.4)

    await channel.send("✅ **phase 1 cleared.**")
    await asyncio.sleep(1.5)

    ARGUMENTS = [
        ("i built this city with my own hands.", "deny"),
        ("a king must take to protect.", "deny"),
        ("history will call me great.", "accept"),
        ("without me, there is nothing.", "judge"),
        ("order requires sacrifice.", "deny"),
    ]

    await channel.send(embed=discord.Embed(
        title="🩸 PHASE 2",
        description="respond with what is correct: `accept`, `deny`, or `judge`",
        color=discord.Color.dark_red()
    ))

    for text, tag in ARGUMENTS:
        await channel.send(embed=discord.Embed(
            description=text,
            color=discord.Color.dark_red()
        ))

        try:
            msg = await bot.wait_for("message", timeout=7, check=check)
            ans = msg.content.lower().strip()

            if ans == tag:
                await channel.send("✅")
            else:
                await channel.send("💀 he convinces you.")
                return False

        except:
            await channel.send("💀 silence becomes consent.")
            return False

        await asyncio.sleep(0.3)

    await channel.send("✅ **phase 2 cleared.**")
    await asyncio.sleep(1.5)

    await channel.send(embed=discord.Embed(
        title="PHASE 3",
        description="catch it or leave it",
        color=discord.Color.dark_red()
    ))

    for i in range(1):
        event = random.choice(["fake_throw", "real_throw", "delayed_throw"])

        if event == "fake_throw":
            await channel.send("👑 FEINT")
            try:
                msg = await bot.wait_for("message", timeout=2, check=check)
                if msg.content.lower().strip() == "catch":
                    return False
            except:
                pass

        elif event == "real_throw":
            await channel.send("👑 HE THROWS THE CROWN")
            try:
                msg = await bot.wait_for("message", timeout=4, check=check)
                if msg.content.lower().strip() != "catch":
                    return False
            except:
                return False

        elif event == "delayed_throw":
            await channel.send("👑 ...nothing yet")
            await asyncio.sleep(2)
            await channel.send("👑 NOW")
            try:
                msg = await bot.wait_for("message", timeout=3, check=check)
                if msg.content.lower().strip() != "catch":
                    return False
            except:
                return False

        await channel.send("✅")

    await channel.send(embed=discord.Embed(
        description="👑 **minnea kneels.**",
        color=discord.Color.gold()
    ))

    return True


async def run_dealer_sr(bot, channel, member) -> bool:
    def check(m):
        return m.author.id == member.id and m.channel == channel

    CARDS = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
    VAL = {"A":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"10":10,"J":11,"Q":12,"K":13}

    await channel.send(embed=discord.Embed(
        title="🃏 DEALER SR.",
        description="*the table shifts. the rules change.*",
        color=discord.Color.dark_grey()
    ))

    await asyncio.sleep(2)

    await channel.send(embed=discord.Embed(
        title="PHASE 1",
        color=discord.Color.dark_grey()
    ))

    for _ in range(4):
        c1 = random.choice(CARDS)
        c2 = random.choice(CARDS)

        await channel.send(f"🃏 `{c1}` -> next card higher or lower? (`higher` / `lower`)")

        try:
            msg = await bot.wait_for("message", timeout=5, check=check)
            ans = msg.content.lower().strip()
        except:
            return False

        if (VAL[c2] > VAL[c1] and ans != "higher") or (VAL[c2] < VAL[c1] and ans != "lower"):
            await channel.send(f"💀 wrong. it was `{c2}`")
            return False

        await channel.send("✅")

        hand = random.choices(CARDS, k=2)
        total = sum(VAL[c] for c in hand)

        await channel.send(f"🂡 hand: `{hand}` ({total}) -> `hit` or `stand`?")

        try:
            msg = await bot.wait_for("message", timeout=5, check=check)
            ans = msg.content.lower().strip()
        except:
            return False

        correct = "hit" if total < 17 else "stand"

        if ans != correct:
            await channel.send(f"💀 wrong. correct: `{correct}`")
            return False

        await channel.send("✅")

    await channel.send("✅ **phase 1 cleared.**")
    await asyncio.sleep(1.5)

    await channel.send(embed=discord.Embed(
        title="PHASE 2",
        color=discord.Color.dark_grey()
    ))

    HANDS = ["pair of kings", "flush", "full house", "nothing"]

    for _ in range(5):
        real = random.random() < 0.5
        hand = random.choice(HANDS)

        shown = hand if real else f"{hand} (bluff)"

        await channel.send(f"🃏 {shown}\n`call` or `fold`?")

        try:
            msg = await bot.wait_for("message", timeout=6, check=check)
            ans = msg.content.lower().strip()
        except:
            return False

        correct = "call" if real else "fold"

        if ans != correct:
            await channel.send("💀 you misread him.")
            return False

        await channel.send("✅")

    await channel.send("✅ **phase 2 cleared.**")
    await asyncio.sleep(1.5)

    await channel.send(embed=discord.Embed(
        title="PHASE 3",
        color=discord.Color.dark_red()
    ))

    ATTACKS = [
        ("aphrodite", "💋 *\"stay with me.\"*", "resist", "`resist, deny, ignore, look away`"),
        ("genghis khan", "🏹 ARROW RAIN", "shield", "`scatter, shield, break, hold`"),
        ("caligula", "you must obey", "deny", "`deny, judge, ignore`"),
        ("king minnea", "👑 HE THROWS THE CROWN", "catch", "`wait, catch`"),
    ]

    for _ in range(4):
        name, text, correct, choices22 = random.choice(ATTACKS)

        embed = discord.Embed(
            title=name.upper(),
            description=text,
            color=discord.Color.red()
        )

        embed.add_field(
            name="options",
            value=choices22,
            inline=False
        )

        embed.set_footer(text="respond correctly to survive.")

        await channel.send(embed=embed)

        try:
            msg = await bot.wait_for("message", timeout=3, check=check)
            ans = msg.content.lower().strip()
        except:
            return False

        if ans != correct:
            await channel.send(embed=discord.Embed(
                description="💀 overwhelmed.",
                color=discord.Color.dark_red()
            ))
            return False

        await channel.send(embed=discord.Embed(
            description="✅",
            color=discord.Color.green()
        ))

    await channel.send(embed=discord.Embed(
        description="✅ **phase 3 cleared.**",
        color=discord.Color.green()
    ))

    await channel.send(embed=discord.Embed(
        description="🏆 you have defeated the fraud (ba dum tss)",
        color=discord.Color.gold()
    ))

    return True


async def run_anti_vlad(bot, channel, member) -> bool | str:
    def check(m):
        return m.author.id == member.id and m.channel == channel

    await channel.send(embed=discord.Embed(
        title="🗡️ PHASE 1",
        description=(
            "`deny` -> reject the claim\n"
            "`counter` -> counter his claim\n\n"
            "anything else = death"
        ),
        color=discord.Color.from_rgb(0, 0, 0)
    ))

    await asyncio.sleep(2)

    STRIKES = [
        ("the Order brought peace.", "deny"),
        ("you exist because of them.", "deny"),
        ("there was no alternative.", "counter"),
        ("you are standing on their foundation.", "deny"),
        ("removing them caused more harm than good.", "counter"),
        ("you already agree with me.", "deny"),
        ("i am indispensable.", "counter"),
        ("the Order brings salvation to this world.", "deny")
    ]

    random.shuffle(STRIKES)

    for attack, correct in STRIKES:

        await channel.send(embed=discord.Embed(
            description=f"🗡️ *{attack}*",
            color=discord.Color.from_rgb(0, 0, 0)
        ))

        try:
            msg = await bot.wait_for("message", timeout=5, check=check)
            ans = msg.content.lower().strip()
        except asyncio.TimeoutError:
            await channel.send(embed=discord.Embed(
                description="💀 *you hesitated. he ends it.*",
                color=discord.Color.from_rgb(0, 0, 0)
            ))
            return False

        if ans != correct:
            await channel.send(embed=discord.Embed(
                description="💀 *wrong response. he reads your weakness instantly.*",
                color=discord.Color.from_rgb(0, 0, 0)
            ))
            return False

        await channel.send("⚡")

        await asyncio.sleep(0.2)

    await asyncio.sleep(2)
    await channel.send(embed=discord.Embed(
        title="🗡️ PHASE 2",
        description=(
            "*\"good,\"* he says. *\"you understand what they did.\"*\n\n"
            "*\"i want to restore what was taken. "
            "it will take time. it will take help.\"*\n\n"
            "**he extends a hand.**\n\n"
            "*\"fight me if you must. or join what i'm building.\"*\n\n"
            "type `fight` or `join`."
        ),
        color=discord.Color.from_rgb(0, 0, 0)
    ))

    try:
        msg = await bot.wait_for("message", timeout=30, check=check)
        choice = msg.content.lower().strip()
    except asyncio.TimeoutError:
        choice = "fight"

    if choice == "join":
        await channel.send(embed=discord.Embed(
            description=(
                "*\"then we begin.*\"\n"
                "***to be concluded in 1.7.***"
            ),
            color=discord.Color.from_rgb(0, 0, 0)
        ))
        return "joined"

    DUEL_MOVES = {
        "🗡️ LUNGE":    "parry",
        "🛡️ SHIELD":   "break",
        "⚡ FEINT":    "wait",
        "🔄 SPIN":     "duck",
        "💨 RETREAT":  "advance",
    }
    await channel.send(embed=discord.Embed(
        title="🗡️ PHASE 3",
        description="he draws.",
        color=discord.Color.from_rgb(0, 0, 0)
    ))
    await asyncio.sleep(2)

    exchanges = random.choices(list(DUEL_MOVES.items()), k=5)
    for move, counter in exchanges:
        await channel.send(embed=discord.Embed(description=f"**`{move}`**. type: `{counter}`", color=discord.Color.from_rgb(0, 0, 0)))
        try:
            msg = await bot.wait_for("message", timeout=4, check=check)
            if msg.content.lower().strip() == counter:
                await channel.send(embed=discord.Embed(description="✅", color=discord.Color.green()))
            else:
                await channel.send(embed=discord.Embed(
                    description=f"💀 *he disarms you.* correct: `{counter}`",
                    color=discord.Color.from_rgb(0, 0, 0)
                ))
                return False
        except asyncio.TimeoutError:
            await channel.send(embed=discord.Embed(description=f"⏰ too slow. correct: `{counter}`", color=discord.Color.from_rgb(0, 0, 0)))
            return False
        await asyncio.sleep(0.3)

    await channel.send(embed=discord.Embed(
        description=(
            "*he falls to one knee, blade in the ground.*\n\n"
            "*\"good. the world needs people who can fight for it.\"*\n"
            "***to be concluded in 1.7.***"
        ),
        color=discord.Color.gold()
    ))
    return "won"

class HellBossView(discord.ui.View):
    def __init__(self, bot, layer: dict, member: discord.Member):
        super().__init__(timeout=60)
        self.bot    = bot
        self.layer  = layer
        self.member = member

    @discord.ui.button(label="fight", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def fight_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            return await interaction.response.send_message("not your fight.", ephemeral=True)

        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT last_fight FROM enemy_cooldowns WHERE user_id=$1 AND enemy=$2",
                self.member.id, f"hell_{self.layer['name']}"
            )
        if row:
            cooldown_end = row["last_fight"] + timedelta(hours=48)
            if cooldown_end > dt.now(timezone.utc):
                ts = int(cooldown_end.timestamp())
                return await interaction.response.send_message(f"on cooldown. try again <t:{ts}:R>", ephemeral=True)

        self.stop()
        await interaction.response.send_message(embed=discord.Embed(
            description=f"{self.layer['emoji']} **the fight begins...**",
            color=discord.Color.from_rgb(180, 0, 0)
        ), ephemeral=True)

        boss = self.layer["boss"]
        channel = interaction.channel

        fight_fns = {
            "aphrodite": run_aphrodite,
            "genghis_khan": run_genghis_khan,
            "caligula": run_caligula,
            "king_minnea": run_king_minnea,
            "dealer_sr": run_dealer_sr,
            "anti_vlad": run_anti_vlad,
        }
        result = await fight_fns[boss](self.bot, channel, self.member)

        if result in (True, "won", "joined"):
            async with db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO enemy_cooldowns (user_id, enemy, last_fight)
                    VALUES ($1,$2,$3)
                    ON CONFLICT (user_id,enemy)
                    DO UPDATE SET last_fight=EXCLUDED.last_fight
                    """,
                    self.member.id,
                    f"hell_{self.layer['name']}",
                    dt.now(timezone.utc)
                )

        if result == "joined":
            await mark_layer_cleared(self.member.id, self.layer["name"])
            cleared_count = await get_cleared_count(self.member.id)

            if cleared_count >= 9:
                hellevator_role = interaction.guild.get_role(HELL_HELLEVATOR_ROLE)
                if hellevator_role and hellevator_role not in self.member.roles:
                    await self.member.add_roles(hellevator_role)
                await channel.send(embed=discord.Embed(
                    title="🔥 HELLEVATOR UNLOCKED",
                    description=f"**{self.member.display_name}** has cleared all 9 layers of hell.",
                    color=discord.Color.gold()
                ))
                await hooks.on_full_descent(self.bot, self.member)

            evil_reward = 500
            await add_evil_quid(self.member.id, evil_reward)
            async with db.pool.acquire() as conn:
                await conn.execute("INSERT INTO user_unlocks (user_id, anti_vlad_joined) VALUES ($1,TRUE) ON CONFLICT (user_id) DO UPDATE SET anti_vlad_joined=TRUE", self.member.id)
            await channel.send(embed=discord.Embed(
                title="🗡️ YOU JOINED THE ANTI-VLAD",
                description=(
                    f"**{self.member.mention}** took his hand.\n\n"
                    f"the rebuilding begins.\n\n"
                    f"{EVIL_EMOJI} **+{evil_reward} evil quid**\n"
                ),
                color=discord.Color.from_rgb(0, 0, 0)
            ))
            await hooks.on_anti_vlad_joined(self.bot, self.member)

        elif result == "won" or result is True:
            await mark_layer_cleared(self.member.id, self.layer["name"])
            cleared_count = await get_cleared_count(self.member.id)

            if cleared_count >= 9:
                hellevator_role = interaction.guild.get_role(HELL_HELLEVATOR_ROLE)
                if hellevator_role and hellevator_role not in self.member.roles:
                    await self.member.add_roles(hellevator_role)

                await channel.send(embed=discord.Embed(
                    title="🔥 HELLEVATOR UNLOCKED",
                    description=f"**{self.member.display_name}** has cleared all 9 layers of hell.",
                    color=discord.Color.gold()
                ))

                await hooks.on_full_descent(self.bot, self.member)

            evil_reward = {
                "aphrodite": 150,
                "genghis_khan":200,
                "caligula": 175,
                "king_minnea": 225,
                "dealer_sr": 200,
                "anti_vlad": 500,
            }.get(boss, 150)
            await add_evil_quid(self.member.id, evil_reward)
            await channel.send(embed=discord.Embed(
                title=f"🏆 {boss.upper().replace('_',' ')} DEFEATED",
                description=(
                    f"**{self.member.mention}** conquered **{self.layer['name']}**.\n\n"
                    f"{EVIL_EMOJI} **+{evil_reward} evil quid**\n"
                    "use `!descend` to proceed."
                ),
                color=discord.Color.gold()
            ))
            await hooks.on_hell_boss_defeat(self.bot, self.member, self.layer["name"])

        else:
            await channel.send(embed=discord.Embed(
                title="💀 DEFEATED",
                description=f"**{self.member.mention}** fell in **{self.layer['name']}**.",
                color=discord.Color.dark_red()
            ))


class HellevatorView(discord.ui.View):
    def __init__(self, bot, member: discord.Member, cleared_layers: list[dict]):
        super().__init__(timeout=60)
        self.bot    = bot
        self.member = member

        options = [
            discord.SelectOption(
                label=f"layer {l['layer_num']} - {l['name']}",
                value=l["name"],
                emoji=l["emoji"],
            )
            for l in cleared_layers
        ]
        self.select.options = options

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.member.id:
            await interaction.response.send_message("this isn't for you.", ephemeral=True)
            return False
        return True

    @discord.ui.select(placeholder="choose a layer...", min_values=1, max_values=1, options=[])
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        target_name = select.values[0]
        layer = get_hell_layer_by_name(target_name)
        if not layer:
            return await interaction.response.send_message("layer not found.", ephemeral=True)

        async with db.pool.acquire() as conn:
            bal = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", self.member.id) or 0
            if bal < 100:
                return await interaction.response.send_message(f"❌ you need 100 {QUID_EMOJI} to use the hellevator.", ephemeral=True)

        guild = interaction.guild
        hell_roles = [guild.get_role(l["role"]) for l in HELL_LAYERS if guild.get_role(l["role"])]
        await self.member.remove_roles(*[r for r in hell_roles if r])

        target_role = guild.get_role(layer["role"])
        if target_role:
            await self.member.add_roles(target_role)

        async with db.pool.acquire() as conn:
            await conn.execute("UPDATE economy SET quid = quid - 100 WHERE user_id=$1", self.member.id)

        self.stop()
        await interaction.response.edit_message(
            embed=discord.Embed(
                title=f"{layer['emoji']} HELLEVATOR - {layer['name'].upper()}",
                description=f"**{self.member.display_name}** descends to **{layer['name']}**.\n\n-100 {QUID_EMOJI}",
                color=discord.Color.from_rgb(180, 0, 0)
            ),
            view=None
        )

class HellCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="evilbal", aliases=["ebal", "eb"], help="check your evil quid balance", usage="!evilbal")
    async def evilbal(self, ctx, member: discord.Member | None = None):
        user = member or ctx.author
        amount = await get_evil_quid(user.id)
        await ctx.send(embed=discord.Embed(
            description=f"{EVIL_EMOJI} **{user.display_name}** has **{amount:,} evil quid**",
            color=discord.Color.from_rgb(180, 0, 0)
        ))

    @commands.command(name="hell", help="switch between hell layers", usage="!hell")
    async def hell(self, ctx):
        if HELL_HELLEVATOR_ROLE not in [r.id for r in ctx.author.roles]:
            return await ctx.send("the hellevator is only accessible after you have cleared all 9 layers of hell.")

        cleared_names = set()
        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT layer_name FROM hell_progress WHERE user_id=$1", ctx.author.id)
            cleared_names = {r["layer_name"] for r in rows}

        cleared_layers = [l for l in HELL_LAYERS if l["name"] in cleared_names]
        if not cleared_layers:
            return await ctx.send("you haven't cleared any layers yet.")

        embed = discord.Embed(
            title=f"HELLEVATOR",
            description=f"choose a layer to descend to.\ncosts **100 {QUID_EMOJI}** per trip.",
            color=discord.Color.from_rgb(180, 0, 0)
        )
        await ctx.send(embed=embed, view=HellevatorView(self.bot, ctx.author, cleared_layers))

    @commands.command(name="descend", help="descend to the next layer of hell", usage="!descend")
    async def descend(self, ctx):
        channel_id = ctx.channel.id
        layer = get_hell_layer(channel_id)

        if not layer:
            return await ctx.send("you can only descend from within a layer of hell.")

        role_ids = {r.id for r in ctx.author.roles}
        if layer["role"] not in role_ids:
            return await ctx.send("you don't have access to this layer.")

        cleared = await has_cleared_layer(ctx.author.id, layer["name"])
        if not cleared:
            if layer["mechanic"] == "evil_quid":
                evil = await get_evil_quid(ctx.author.id)

                if evil >= 500:
                    await mark_layer_cleared(ctx.author.id, "limbo")
                else:
                    return await ctx.send(
                        f"❌ to leave **limbo** you must earn **500 {EVIL_EMOJI} evil quid** total.\n"
                        f"you have **{evil:,}**."
                    )
            elif layer["mechanic"] == "fish_discard":
                async with db.pool.acquire() as conn:
                    discarded = await conn.fetchval(
                        "SELECT gluttony_discarded FROM hell_progress_meta WHERE user_id=$1", ctx.author.id
                    ) or 0
                return await ctx.send(
                    f"❌ to leave **gluttony** you must discard **150 fish** using `!discard`.\n"
                    f"you've discarded **{discarded}/150**."
                )
            elif layer["mechanic"] == "greed_pool":
                async with db.pool.acquire() as conn:
                    contributed = await conn.fetchval(
                        "SELECT greed_contributed FROM hell_progress_meta WHERE user_id=$1", ctx.author.id
                    ) or 0
                return await ctx.send(
                    f"❌ to leave **greed** you must contribute **7500 {QUID_EMOJI}** to the greed pool using `!tribute`.\n"
                    f"you've contributed **{contributed:,}/7500**."
                )
            else:
                return await ctx.send(f"❌ you must defeat the boss in **{layer['name']}** first. use `!fight`.")

        if layer["layer_num"] >= len(HELL_LAYERS):
            return await ctx.send("you are in the deepest layer of hell. there is nowhere left to go.")

        next_layer = HELL_LAYERS[layer["layer_num"]]
        next_role  = ctx.guild.get_role(next_layer["role"])
        curr_role  = ctx.guild.get_role(layer["role"])

        if not next_role:
            return await ctx.send("next layer role not configured. contact an admin.")

        if curr_role:
            await ctx.author.remove_roles(curr_role)
        await ctx.author.add_roles(next_role)

        async with db.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO user_inventory (user_id, item_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                ctx.author.id, f"vacation_hell_{next_layer['name']}"
            )

        cleared_count = await get_cleared_count(ctx.author.id)
        if cleared_count >= 9:
            hellevator_role = ctx.guild.get_role(HELL_HELLEVATOR_ROLE)
            if hellevator_role and hellevator_role not in ctx.author.roles:
                await ctx.author.add_roles(hellevator_role)
                await ctx.send(embed=discord.Embed(
                    title="🔥 HELLEVATOR UNLOCKED",
                    description=f"**{ctx.author.display_name}** has cleared all 9 layers of hell.\n\nuse `!hell` to ride the hellevator between layers.",
                    color=discord.Color.gold()
                ))
            await hooks.on_full_descent(self.bot, ctx.author)

        await ctx.send(embed=discord.Embed(
            title=f"{next_layer['emoji']} DESCENDING - {next_layer['name'].upper()}",
            description=(
                f"**{ctx.author.display_name}** descends into **{next_layer['name']}**.\n\n"
                f"blazing tier: **{next_layer['tier']}**\n"
                f"{'boss: **' + next_layer['boss'].replace('_',' ') + '**. use `!fight`' if next_layer['boss'] else 'mechanic layer: no boss'}"
            ),
            color=discord.Color.from_rgb(180, 0, 0)
        ))
        await hooks.on_hell_descend(self.bot, ctx.author, next_layer["name"])

    @commands.command(name="discard", help="discard fish from your bag", usage="!discard <amount|all>")
    async def discard(self, ctx, amount: str = "1"):
        layer = get_hell_layer(ctx.channel.id)
        if not layer or layer["name"] != "gluttony":
            return await ctx.send("you can only discard fish in gluttony.")
        if layer["role"] not in {r.id for r in ctx.author.roles}:
            return await ctx.send("you don't have access to gluttony.")

        async with db.pool.acquire() as conn:
            bag = await conn.fetch("SELECT fish_id, quantity FROM fish_inventory WHERE user_id=$1", ctx.author.id)
        if not bag:
            return await ctx.send("your fish bag is empty.")

        total_fish = sum(r["quantity"] for r in bag)
        if amount.lower() == "all":
            n = total_fish
        else:
            try:
                n = int(amount)
            except ValueError:
                return await ctx.send("usage: `!discard <number|all>`")

        n = min(n, total_fish)
        if n <= 0:
            return await ctx.send("nothing to discard.")

        remaining = n
        async with db.pool.acquire() as conn:
            for row in bag:
                if remaining <= 0:
                    break
                take = min(remaining, row["quantity"])
                new_qty = row["quantity"] - take
                if new_qty <= 0:
                    await conn.execute("DELETE FROM fish_inventory WHERE user_id=$1 AND fish_id=$2", ctx.author.id, row["fish_id"])
                else:
                    await conn.execute("UPDATE fish_inventory SET quantity=$1 WHERE user_id=$2 AND fish_id=$3", new_qty, ctx.author.id, row["fish_id"])
                remaining -= take

            prev = await conn.fetchval("SELECT gluttony_discarded FROM hell_progress_meta WHERE user_id=$1", ctx.author.id) or 0
            new_total = prev + n
            await conn.execute(
                "INSERT INTO hell_progress_meta (user_id, gluttony_discarded) VALUES ($1,$2) ON CONFLICT (user_id) DO UPDATE SET gluttony_discarded=$2",
                ctx.author.id, new_total
            )

        cleared = new_total >= 150
        if cleared and not await has_cleared_layer(ctx.author.id, "gluttony"):
            await mark_layer_cleared(ctx.author.id, "gluttony")
            await ctx.send(embed=discord.Embed(
                description=f"🍖 **{n} fish discarded** ({new_total}/150).\n\n✅ **gluttony cleared.** you have wasted enough. use `!descend`.",
                color=discord.Color.green()
            ))
        else:
            await ctx.send(embed=discord.Embed(
                description=f"🍖 **{n} fish discarded.** total discarded: **{new_total}/150**.",
                color=discord.Color.from_rgb(180, 100, 40)
            ))

    @commands.command(name="tribute", help="contribute quid to the greed pool", usage="!tribute <amount>")
    async def tribute(self, ctx, amount: int = 0):
        layer = get_hell_layer(ctx.channel.id)
        if not layer or layer["name"] != "greed":
            return await ctx.send("you can only pay tribute in greed.")
        if layer["role"] not in {r.id for r in ctx.author.roles}:
            return await ctx.send("you dont have access to greed.")
        if amount <= 0:
            return await ctx.send("usage: `!tribute <amount>`")

        async with db.pool.acquire() as conn:
            bal = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0
            if bal < amount:
                return await ctx.send(f"❌ you only have {bal:,} {QUID_EMOJI}.")

            await conn.execute("UPDATE economy SET quid = quid - $1 WHERE user_id=$2", amount, ctx.author.id)

            prev = await conn.fetchval("SELECT greed_contributed FROM hell_progress_meta WHERE user_id=$1", ctx.author.id) or 0
            new_total = prev + amount
            await conn.execute(
                "INSERT INTO hell_progress_meta (user_id, greed_contributed) VALUES ($1,$2) ON CONFLICT (user_id) DO UPDATE SET greed_contributed=$2",
                ctx.author.id, new_total
            )
            await conn.execute(
                "INSERT INTO greed_pool (total) VALUES ($1) ON CONFLICT (id) DO UPDATE SET total = greed_pool.total + $1",
                amount
            )
            pool_total = await conn.fetchval("SELECT total FROM greed_pool WHERE id=1") or 0

        cleared = new_total >= 7500
        if cleared and not await has_cleared_layer(ctx.author.id, "greed"):
            await mark_layer_cleared(ctx.author.id, "greed")
            await ctx.send(embed=discord.Embed(
                description=(
                    f"🪙 **{amount:,} {QUID_EMOJI} added to the pool.**\n"
                    f"your total tribute: **{new_total:,}/7500 {QUID_EMOJI}**\n"
                    f"pool total: **{pool_total:,} {QUID_EMOJI}**\n\n"
                    f"✅ **greed cleared.** you gave enough. use `!descend`."
                ),
                color=discord.Color.green()
            ))
        else:
            await ctx.send(embed=discord.Embed(
                description=(
                    f"🪙 **{amount:,} {QUID_EMOJI} added to the pool.**\n"
                    f"your total tribute: **{new_total:,}/7500 {QUID_EMOJI}**\n"
                    f"pool total: **{pool_total:,} {QUID_EMOJI}**"
                ),
                color=discord.Color.from_rgb(220, 180, 0)
            ))

async def setup(bot):
    await bot.add_cog(HellCommands(bot))