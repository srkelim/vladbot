import os
import discord
import datetime
import asyncio
from discord.ext import commands, tasks
import typing
import time
import random
import math
from cogs.achievements import hooks
from cogs.economy.economycommands import has_unlock

from config import XP_MIN, XP_MAX, XP_LEVEL_UPS_CHANNEL, XP_LAST_EMOJI, XP_LEVEL_REWARDS
from db import db

AIRole = int(os.getenv("AIRole"))

class XPTopView(discord.ui.View):
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
            res = await conn.fetch(
                """
                SELECT user_id, xp, short_name
                FROM xp
                ORDER BY xp DESC
                OFFSET $1 LIMIT $2
                """,
                skip, self.page_size
            )

        def rank_emoji(pos):
            if pos == 1:
                return "<:diamondvlad:1402318150028234752> "
            if pos == 2:
                return "<:goldvlad:1402318157552685159>"
            if pos == 3:
                return "<:silvervlad:1402318161461907597>"
            return "<:vlad:1402318168097165352>"

        embed = discord.Embed(
            title="xp leaderboard",
            description="who needs grass anyway",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=self.ctx.guild.icon)

        if not res:
            embed.add_field(
                name="empty",
                value="no data on this page",
                inline=False
            )

        for idx, row in enumerate(res, start=1):
            position = idx + (self.page_size * (self.page - 1))
            emoji = rank_emoji(position)

            user = self.ctx.guild.get_member(row["user_id"])
            if not user:
                try:
                    user = await self.bot.fetch_user(row["user_id"])
                except:
                    user = None

            name = (
                user.global_name
                if user and user.global_name
                else user.name if user
                else row["short_name"] or "Quitter"
            )

            level = self.ctx.cog.calc_level_for_xp(row["xp"])

            embed.add_field(
                name=f"{emoji} **#{position} - {name}**",
                value=f"**XP:** {row['xp']:,}\n**Level:** {level}",
                inline=False
            )

        embed.set_footer(
            text=f"page {self.page}/{self.total_pages} • requested by {self.ctx.author.display_name}"
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

class XpCommand(commands.Cog):
    user_cooldowns = {}

    def __init__(self, bot):
        self.bot = bot
        self.min_xp = XP_MIN
        self.max_xp = XP_MAX
        self.level_rewards = XP_LEVEL_REWARDS
        self.after_last_emoji = XP_LAST_EMOJI
        self.level_ups_channel_id = XP_LEVEL_UPS_CHANNEL
        self.remove_old_cooldowns.start()
        self.removexp_cd = commands.CooldownMapping.from_cooldown(
            1, 3600, commands.BucketType.user
        )

    async def cog_unload(self):
        self.remove_old_cooldowns.cancel()

    async def ensure_user(self, user: discord.Member):
        async with db.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user.id
            )
            await conn.execute(
                """
                INSERT INTO xp (user_id, xp, short_name)
                VALUES ($1, 0, $2)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user.id, user.display_name
            )
            await conn.execute(
                """
                INSERT INTO xp_optout (user_id, optout, name)
                VALUES ($1, FALSE, $2)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user.id, user.display_name
            )

    @commands.command(
        name="addxp",
        help="give xp to someone",
        usage="!addxp person xp"
    )
    @commands.has_role(AIRole)
    async def givexp(
        self,
        ctx: commands.Context,
        member: typing.Optional[discord.Member],
        amount_of_xp: int
    ):
        user = member if member is not None else ctx.author
        if not isinstance(user, discord.Member):
            return
        if not ctx.guild:
            return

        embed = discord.Embed(
            title="handing out the xp",
            timestamp=ctx.message.created_at
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
        embed.add_field(name="given by", value=ctx.author.display_name, inline=True)
        embed.add_field(name="taken by", value=user.display_name, inline=True)
        embed.add_field(name="amount", value=amount_of_xp, inline=True)

        await self.add_xp(user, amount_of_xp)

        embed.set_footer(text=ctx.guild.name)
        await ctx.send(embed=embed)

    @commands.command(
        name="xp",
        help="view your or someone else's xp",
        aliases=["showxp"],
        usage="!xp person"
    )
    async def showXp(self, ctx: commands.Context, user: typing.Optional[discord.Member]):
        user = user or ctx.author
        await self.ensure_user(user)

        async with db.pool.acquire() as conn:
            res = await conn.fetchrow(
                "SELECT xp FROM xp WHERE user_id = $1",
                user.id
            )

        if res is None:
            await ctx.reply("blub didnt even talk once lmfaooo")
            return

        xp_val = res["xp"]
        current_level = self.calc_level_for_xp(xp_val)
        next_level_xp = self.calc_xp_for_level(current_level + 1)
        prev_level_xp = self.calc_xp_for_level(current_level)

        progress = xp_val - prev_level_xp
        needed = next_level_xp - prev_level_xp

        async with db.pool.acquire() as conn:
            rank = await conn.fetchval(
                "SELECT COUNT(*) + 1 FROM xp WHERE xp > $1",
                xp_val
            )

        level_emoji = self.level_rewards[0]["emoji"]
        next_level_emoji = self.after_last_emoji

        for reward in self.level_rewards:
            if current_level >= reward["level"]:
                level_emoji = reward["emoji"]
            else:
                next_level_emoji = reward["emoji"]
                break

        bar = self.make_bar(progress, needed)

        embed = discord.Embed(
            color=discord.Color.from_rgb(120, 90, 255),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )

        embed.set_author(
            name=user.display_name,
            icon_url=user.avatar.url if user.avatar else None
        )

        embed.description = (
            f"### {level_emoji} LEVEL **{current_level}**\n"
            f"**rank** `#{rank}`\n\n"
            f"`{bar}`\n"
            f"**{progress:,} / {needed:,} xp** → "
            f"{next_level_emoji} **level {current_level + 1}**"
        )

        embed.add_field(
            name="total xp",
            value=f"`{xp_val:,}`",
            inline=True
        )

        embed.add_field(
            name="to next level",
            value=f"`{needed - progress:,}` xp",
            inline=True
        )

        embed.add_field(
            name="\u200b",
            value=(
                f"**progress:** `{int((progress / needed) * 100)}%`\n"
                f"**aura:** {level_emoji} → {next_level_emoji}"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"requested by {ctx.author.display_name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )

        await ctx.send(embed=embed)

    @commands.command(
        name="xptop",
        help="leaderboard of the lifeless",
        usage="!xptop"
    )
    async def xpTop(self, ctx: commands.Context):
        page_size = 5

        async with db.pool.acquire() as conn:
            total_records = await conn.fetchval(
                "SELECT COUNT(*) FROM xp"
            )

        if total_records == 0:
            return await ctx.send("no xp data exists yet")

        total_pages = (total_records + page_size - 1) // page_size

        view = XPTopView(
            bot=self.bot,
            ctx=ctx,
            total_pages=total_pages,
            page_size=page_size
        )

        embed = await view.generate_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(
        name="optout",
        help="for stopping the pingery",
        usage="!optout"
    )
    async def optout(self, ctx: commands.Context):
        await self.ensure_user(ctx.author)

        async with db.pool.acquire() as conn:
            new_val = await conn.fetchval(
                """
                UPDATE xp_optout
                SET optout = NOT optout
                WHERE user_id = $1
                RETURNING optout
                """,
                ctx.author.id
            )

        await ctx.send(
            "sure you wont be pinged no more"
            if new_val else
            "alright you will be pinged"
        )

    @commands.command(
        name="tradexp",
        help="trade xp with someon",
        usage="!tradexp person xp"
    )
    async def tradexp(self, ctx, member: discord.Member, amount: int):
        if member.bot:
            return await ctx.send("you can't trade xp with bots")

        if member.id == ctx.author.id:
            return await ctx.send("you can't trade xp with yourself")

        if amount <= 0:
            return await ctx.send("please enter a positive amount of xp to trade")

        await self.ensure_user(ctx.author)
        await self.ensure_user(member)

        async with db.pool.acquire() as conn:
            sender_xp = await conn.fetchval(
                "SELECT xp FROM xp WHERE user_id = $1",
                ctx.author.id
            )

            if sender_xp < amount:
                return await ctx.send(
                    f"you don't have enough xp to trade. you have {sender_xp} xp."
                )

            await conn.execute(
                "UPDATE xp SET xp = xp - $1 WHERE user_id = $2",
                amount, ctx.author.id
            )
            await conn.execute(
                "UPDATE xp SET xp = xp + $1 WHERE user_id = $2",
                amount, member.id
            )

        await ctx.send(
            f"✅ {ctx.author.mention} gave **{amount} xp** to {member.mention}!!!!!"
        )

    @commands.command(
        name="removexp",
        help="remove 1 xp from someone",
        usage="!removexp @user/userID"
    )
    async def removexp(self, ctx, member: discord.Member):
        await self.ensure_user(member)

        bucket = self.removexp_cd.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()

        if retry_after:
            end_ts = int(time.time() + retry_after)
            return await ctx.send(f"⏱️ cooldown!! try again **<t:{end_ts}:R>**")

        async with db.pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE xp SET xp = xp - 1 WHERE user_id = $1 AND xp > 0",
                member.id
            )

        if result.endswith("0"):
            bucket.reset()
            return await ctx.send("user has no xp")

        if member.id == ctx.bot.user.id:
            await ctx.send("✅ hey! you just took XP from **me**... rude 😢")
            await hooks.on_remove_xp_from_vladbot(self.bot, ctx.author)
        else:
            await ctx.send(f"✅ 1 xp has been removed from {member.mention} by {ctx.author.mention}!!!!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            message.author.bot
            or message.guild is None
            or not isinstance(message.author, discord.Member)
        ):
            return

        if (
            message.author.id in self.user_cooldowns
            and time.time() <= self.user_cooldowns[message.author.id]
        ):
            return

        self.user_cooldowns[message.author.id] = time.time()
        added_xp = random.randint(self.min_xp, self.max_xp)

        await self.add_xp(message.author, added_xp)


    async def get_xp_multiplier(self, conn, user_id: int) -> float:
        boost = await conn.fetchval(
            "SELECT xp_boost FROM user_unlocks WHERE user_id = $1",
            user_id
        )
        return 2 if boost else 1

    async def add_xp(self, user: discord.Member, xp: int, force_give_roles: bool = False):
        await self.ensure_user(user)
        async with db.pool.acquire() as conn:
            old_xp = await conn.fetchval("SELECT xp FROM xp WHERE user_id = $1", user.id)
            mult = await self.get_xp_multiplier(conn, user.id)
            boosted_xp = int(xp * mult)

            new_xp = await conn.fetchval(
                """
                INSERT INTO xp (user_id, xp)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET xp = xp.xp + EXCLUDED.xp
                RETURNING xp
                """,
                user.id, boosted_xp
            )

        current_level = self.calc_level_for_xp(new_xp)
        old_level = self.calc_level_for_xp(old_xp)

        if current_level == old_level and not force_give_roles:
            return

        current_roles = {role.id for role in user.roles}

        to_add = [
            role
            for reward in self.level_rewards
            if reward["level"] <= current_level
            and (role := user.guild.get_role(reward["role"])) is not None
            and role.id not in current_roles
        ]

        to_remove = [
            role
            for reward in self.level_rewards
            if reward["level"] > current_level
            and (role := user.guild.get_role(reward["role"])) is not None
            and role.id in current_roles
        ]

        if to_add:
            await user.add_roles(*to_add)
        if to_remove:
            await user.remove_roles(*to_remove)

        if current_level > old_level:
            if not self.level_ups_channel_id:
                return

            channel = user.guild.get_channel(self.level_ups_channel_id)
            if not isinstance(channel, discord.TextChannel):
                return

            async with db.pool.acquire() as conn:
                data = await conn.fetchrow(
                    "SELECT optout FROM xp_optout WHERE user_id = $1",
                    user.id
                )

            await channel.send(
                f"🎉 congrats, "
                f"{user.name if data and data['optout'] else user.mention}! "
                f"you leveled up or smth! you're now **{current_level}**."
            )

            await hooks.on_level_up(
                self.bot,
                user,
                current_level
            )
        
    def calc_level_for_xp(self, xp: int) -> int:
        mult = -1 if xp < 0 else 1
        xp *= mult
        return math.floor(math.sqrt((xp / 5) + 25) - 5) * mult

    def calc_xp_for_level(self, level: int) -> int:
        if level < 0:
            return self.calc_xp_for_level(-level) * -1
        return 5 * (level * level + level * 10)
        

    def make_bar(self, current: int, total: int, size: int = 14):
        if total <= 0:
            return "▱" * size
        filled = int((current / total) * size)
        filled = min(max(filled, 0), size)
        return "▰" * filled + "▱" * (size - filled)

    @tasks.loop(seconds=120.0)
    async def remove_old_cooldowns(self):
        to_remove = [
            userid
            for userid, cooldown in self.user_cooldowns.items()
            if time.time() > cooldown
        ]
        for user in to_remove:
            del self.user_cooldowns[user]


async def setup(bot):
    await bot.add_cog(XpCommand(bot))