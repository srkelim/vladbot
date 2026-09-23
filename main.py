import traceback
import discord
import time
from discord.ext import commands
import os
from dotenv import load_dotenv
import yaml
from pathlib import Path
from cogs.fun.funcommands import ParthenonView, setup_parthenon_message
from config import DREAMSKY_CHANNEL, OWNER_ID

from db import db

load_dotenv(override=True)

CONFIG_PATH = Path(__file__).parent / "config.yml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

class Bot(commands.Bot):
    def __init__(self):
        self.config = CONFIG
        self.start_time = time.time()
        prefixes = os.getenv("PREFIXES", "!").split(",")
        super().__init__(
            command_prefix=[p.strip() for p in prefixes],
            intents=discord.Intents.all()
        )
        self.remove_command("help")
        self.sniped_messages = {}

    async def on_ready(self):
        print(f"Connected as {bot.user}")

        channel = bot.get_channel(DREAMSKY_CHANNEL)
        if not channel:
            return

        bot.add_view(ParthenonView(bot))

        async for msg in channel.history(limit=100):
            if msg.author == bot.user and msg.components:
                return

        await setup_parthenon_message(bot, channel)

    async def setup_hook(self):
        await db.connect()

        from cogs.achievements.manager import AchievementManager
        self.achievement_manager = AchievementManager(self)
        await self.achievement_manager.sync_registry()

        for folder in Path("./cogs").iterdir():
            if not folder.is_dir():
                continue

            for file in folder.iterdir():
                if not file.name.endswith(("commands.py", "Events.py")):
                    continue

                module = f"cogs.{folder.name}.{file.stem}"
                try:
                    await self.load_extension(module)
                    print(f"Loaded {module}")
                except Exception as e:
                    print(f"Failed to load {module}")
                    print(f"[ERROR] {e}")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.CommandOnCooldown):
            end_ts = int(time.time() + error.retry_after)
            await ctx.send(
                f"⏱️ cooldown!! try again **<t:{end_ts}:R>**"
            )
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send(f"blub thats just so wrong oh my | correct usage: {ctx.command.usage}")
            return

        if isinstance(error, commands.MissingRole):
            await ctx.reply("blub this command can only be used by the creator")
            return

        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.reply("blub you cant use this command in dms")

        user_id = OWNER_ID
        user = ctx.guild.get_member(user_id)

        try:
            async with db.pool.acquire() as conn:
                await conn.execute("""
                INSERT INTO error_counter (id, error_count)
                VALUES ('err', 0)
                ON CONFLICT (id) DO NOTHING;
                """)

                row = await conn.fetchrow(
                    "SELECT error_count FROM error_counter WHERE id = 'err'"
                )

                error_count = row["error_count"]
                error_code = str(error_count).zfill(3)

                await conn.execute(
                    "UPDATE error_counter SET error_count = error_count + 1 WHERE id = 'err'"
                )

            if user:
                full_error_message = "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                )

                await user.send(
                    f"sent by {ctx.author}\n"
                    f"message link: {ctx.message.jump_url}\n"
                    f"error code: {error_code}\n"
                    f"```{full_error_message[:1500]}```"
                )

                await ctx.reply(f"some weird shit and an error happened idk: VLAD-ERR-{error_code}")

        except Exception as e:
            print(f"[ERROR LOGGING FAILED] {e}")


bot = Bot()
bot.run(os.getenv("TOKEN"))