from discord.ext import commands
import os
from datetime import time as dt_time
import random
import time
import re

from config import SIGWATER_CHANNEL, SIGWATER_ROLE, HEAVEN_CHANNEL, HEAVEN_ROLE, ICY_PEAKS_CHANNEL, ICY_PEAKS_ROLE, QUID_EMOJI
from db import db

AIRole = int(os.getenv("AIRole"))
prefixes = ["!"]
buttons = ["⬆️", "⬇️"]
BAD_WORDS = ["fuck", "shit", "bitch", "cunt", "asshole", "ass", "shithead", "wtf", "hell"]
BAD_WORDS_REGEX = re.compile(rf"\b({'|'.join(map(re.escape, BAD_WORDS))})\b", re.IGNORECASE)

HEAVEN_QUOTES = [
    "you feel light.",
    "time does not move here.",
    "your sins are archived.",
    "welcome home.",
    "you will forget this place.",
    "he is watching.",
    "your name was written in the book.",
    "the sky remembers you."
]

class messageEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sigwater_cooldowns = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        user_id = message.author.id

        heaven_message_counter = {}

        if message.author.bot:
            return
        if message.guild is None:
            return

        if message.channel.id == SIGWATER_CHANNEL and SIGWATER_ROLE in [r.id for r in message.author.roles]:
            await self.sigwater_events(message)

        if message.channel.id == HEAVEN_CHANNEL and HEAVEN_ROLE in [r.id for r in message.author.roles]:
            await self.heaven_events(message)

        if message.channel.id == ICY_PEAKS_CHANNEL and ICY_PEAKS_ROLE in [r.id for r in message.author.roles]:
            await self.icy_peaks_events(message)

        async def fetch_quick_commands_from_db():
            try:
                async with db.pool.acquire() as conn:
                    rows = await conn.fetch(
                        "SELECT command_name FROM quick_commands"
                    )
                return [row["command_name"] for row in rows]
            except Exception as e:
                return []

        if message.content.startswith(tuple(prefixes)):
            prefix = next((p for p in prefixes if message.content.startswith(p)), None)
            if not prefix:
                return

            command_body = message.content[len(prefix):]

            try:
                quick_commands = await fetch_quick_commands_from_db()
            except Exception as e:
                return

            if command_body in quick_commands:
                print(f"Executing quick command: {command_body}")
                await QuickOrFeedbackCommands(message=message)
                return

        await yoSystem_Handler(message)

    async def sigwater_events(self, message):
        fishing_users = getattr(self.bot, "_fishing_users", set())
        if message.author.id in fishing_users:
            return
        user = message.author
        now = time.time()

        last = self.sigwater_cooldowns.get(user.id, 0)
        if now - last < 3:
            return
        self.sigwater_cooldowns[user.id] = now

        async with db.pool.acquire() as conn:
            current_quid = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1",
                user.id
            ) or 0

            if current_quid <= -5000:
                return

            loss = int(abs(current_quid) * 0.04)
            loss = max(20, loss)

            await conn.execute(
                "UPDATE economy SET quid = quid - $1 WHERE user_id = $2",
                loss,
                user.id
            )

        await message.channel.send(
            f"sigwater drains **{loss}** {QUID_EMOJI} from {user.mention}."
        )

    async def heaven_events(self, message):
        uid = message.author.id
        now = time.time()
        self.heaven_message_counter.setdefault(uid, [])
        self.heaven_message_counter[uid].append(now)
        self.heaven_message_counter[uid] = [t for t in self.heaven_message_counter[uid] if now - t < 30]

        if len(self.heaven_message_counter[uid]) > 8:
            await message.author.remove_roles(message.guild.get_role(HEAVEN_ROLE))
            await message.author.send("you spoke too much. heaven is quiet.")
            self.heaven_message_counter.pop(uid, None)
            return

        if BAD_WORDS_REGEX.search(message.content):
            sin_count = await db.pool.fetchval(
                "SELECT sins FROM heaven_sins WHERE user_id=$1", uid
            ) or 0
            sin_count += 1
            await db.pool.execute(
                """
                INSERT INTO heaven_sins(user_id, sins)
                VALUES ($1, $2)
                ON CONFLICT(user_id) DO UPDATE SET sins = $2
                """,
                uid, sin_count
            )

            if sin_count >= 4:
                await message.author.remove_roles(message.guild.get_role(HEAVEN_ROLE))
                await message.author.send("you have sinned too much and have been removed from heaven")
                return
            else:
                await message.channel.send(f"⚠️ {message.author.mention}, heaven is MAD at you for your words")

        if random.random() < 0.05:
            reward = random.randint(50, 150)
            await db.pool.execute(
                "UPDATE economy SET quid = quid + $1 WHERE user_id=$2",
                reward, uid
            )
            await message.channel.send(f"🕊️ {message.author.mention} is blessed by heaven! +{reward} {QUID_EMOJI}")

        if random.random() < 0.04:
            await message.channel.send(f"🪽 {random.choice(HEAVEN_QUOTES)}")

    async def icy_peaks_events(self, message):
        uid = message.author.id
        async with db.pool.acquire() as conn:
            weather = self.icy_peaks_weather.get(message.channel.id, "clear")
            if random.random() < 0.05:
                weather = random.choice(["blizzard", "clear", "calm"])
                self.icy_peaks_weather[message.channel.id] = weather
                await message.channel.send(f"weather changed to {weather}.")

            if weather == "blizzard" and random.random() < 0.15:
                loss = random.randint(20, 40)
                await conn.execute(
                    "UPDATE economy SET quid = quid - $1 WHERE user_id=$2",
                    loss, uid
                )
                await message.channel.send(f"🥶 {message.author.mention} lost {loss} {QUID_EMOJI} to hypothermia!")

            if weather in ["clear", "calm"] and random.random() < 0.1:
                gain = random.randint(50, 150)
                await conn.execute(
                    "UPDATE economy SET quid = quid + $1 WHERE user_id=$2",
                    gain, uid
                )
                await message.channel.send(f"🧊 {message.author.mention} explored the peaks and found {gain} {QUID_EMOJI}!")

            if random.random() < 0.03:
                await message.channel.send(f"❄️ {message.author.mention} slipped on ice! react ⚡ to regain balance.")
                await message.add_reaction("⚡")

                def check_slip(reaction, user):
                    return user.id == uid and str(reaction.emoji) == "⚡" and reaction.message.id == message.id

                try:
                    await self.bot.wait_for("reaction_add", timeout=5.0, check=check_slip)
                    await message.channel.send(f"✅ {message.author.mention} regained balance!")
                except:
                    loss = random.randint(65, 110)
                    await conn.execute(
                        "UPDATE economy SET quid = quid - $1 WHERE user_id=$2",
                        loss, uid
                    )
                    await message.channel.send(f"💥 {message.author.mention} fell and lost {loss} {QUID_EMOJI}!")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        self.bot.sniped_messages[message.channel.id] = message

async def yoSystem_Handler(message):
    try:
        content = message.content.lower()
        yo_variations = {
            "yo", "yoy", "yoyo", "oy",
            ":yo:", ":yonas:", ":yoboss:", ":squidyo:", ":shellyo:"
        }

        words = [w.strip(".,!?") for w in content.split()]

        if any(word in yo_variations for word in words):
            async with db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO yo_global (word, yo_count)
                    VALUES ('yo', 1)
                    ON CONFLICT (word)
                    DO UPDATE SET yo_count = yo_global.yo_count + 1
                    """
                )

                await conn.execute(
                    """
                    INSERT INTO yo_user (user_id, yo_count)
                    VALUES ($1, 1)
                    ON CONFLICT (user_id)
                    DO UPDATE SET yo_count = yo_user.yo_count + 1
                    """,
                    message.author.id
                )

            return True

    except Exception as e:
        print(f"[YO SYSTEM ERROR] {e}")

    return False

async def QuickOrFeedbackCommands(message):
    try:
        command_parts = message.content[len(prefixes[0]):].split()
        cmd = command_parts[0] if command_parts else None
        args = " ".join(command_parts[1:])

        async with db.pool.acquire() as conn:
            quick_cmd = await conn.fetchrow(
                "SELECT command_respond FROM quick_commands WHERE command_name = $1",
                cmd
            )

            if quick_cmd:
                await message.channel.send(quick_cmd["command_respond"])
                return

        await message.reply("Unknown command. Please try again.")

    except Exception as e:
        print(f"Error in QuickOrFeedbackCommands: {e}")


async def setup(bot):
    await bot.add_cog(messageEvents(bot))
