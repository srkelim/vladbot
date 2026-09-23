import discord
from db import db
from cogs.achievements.registry import ACHIEVEMENTS, BONUS_ACHIEVEMENT_IDS
from config import QUID_EMOJI, GENERAL_CHANNEL_ID

class AchievementManager:
    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def sync_registry(self):
        async with db.pool.acquire() as conn:
            for ach in ACHIEVEMENTS.values():
                await conn.execute(
                    """
                    INSERT INTO achievements (
                        id, name, description, category, points, hidden
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        points = EXCLUDED.points,
                        hidden = EXCLUDED.hidden
                    """,
                    ach.id, ach.name, ach.description,
                    ach.category, ach.points, ach.hidden
                )

            registered_ids = list(ACHIEVEMENTS.keys())
            await conn.execute(
                "DELETE FROM achievements WHERE id != ALL($1::text[])",
                registered_ids
            )

    async def has_achievement(self, user_id: int, achievement_id: str) -> bool:
        async with db.pool.acquire() as conn:
            return await conn.fetchval(
                """
                SELECT 1
                FROM user_achievements
                WHERE user_id = $1 AND achievement_id = $2
                """,
                user_id,
                achievement_id
            ) is not None

    async def unlock(
        self,
        *,
        user: discord.Member,
        achievement_id: str
    ) -> bool:

        ach = ACHIEVEMENTS.get(achievement_id)
        if not ach:
            raise RuntimeError(f"Achievement '{achievement_id}' not found in registry")

        if await self.has_achievement(user.id, achievement_id):
            return False

        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_achievements (user_id, achievement_id)
                VALUES ($1, $2)
                """,
                user.id,
                achievement_id
            )

            if ach.reward_xp:
                await conn.execute(
                    """
                    UPDATE xp
                    SET xp = xp + $1
                    WHERE user_id = $2
                    """,
                    ach.reward_xp,
                    user.id
                )

            if ach.reward_quid:
                await conn.execute(
                    """
                    UPDATE economy
                    SET quid = quid + $1
                    WHERE user_id = $2
                    """,
                    ach.reward_quid,
                    user.id
                )

        embed = discord.Embed(
            title="🏆 achievement unlocked",
            color=discord.Color.gold()
        )

        embed.description = f"**{ach.name}**\n{ach.description}"

        rewards = []
        if ach.reward_xp:
            rewards.append(f"💰 **xp:** {ach.reward_xp}")
        if ach.reward_quid:
            rewards.append(f"{QUID_EMOJI} **quid:** {ach.reward_quid}")

        if rewards:
            embed.add_field(
                name="rewards",
                value="\n".join(rewards),
                inline=False
            )

        embed.set_author(
            name=user.display_name,
            icon_url=user.display_avatar.url
        )

        try:
            await user.send(
                content="🏆 you unlocked an achievement!",
                embed=embed
            )
        except discord.Forbidden:
            pass

        async with db.pool.acquire() as conn:
            normal_total = len([a for a in ACHIEVEMENTS if a not in BONUS_ACHIEVEMENT_IDS])

            normal_owned = await conn.fetchval(
                """
                SELECT COUNT(*) FROM user_achievements
                WHERE user_id = $1
                AND achievement_id != ALL($2::text[])
                """,
                user.id,
                list(BONUS_ACHIEVEMENT_IDS),
            )

        if normal_owned >= normal_total:
            channel = self.bot.get_channel(GENERAL_CHANNEL_ID)
            if isinstance(channel, discord.TextChannel):
                embed = discord.Embed(
                    title="👑 ACHIEVEMENT MASTER",
                    description=f"**{user.display_name} unlocked EVERY achievement!!!!!!**\n\n*last page of shop unlocked.*",
                    color=discord.Color.yellow()
                )

                embed.set_author(
                    name=user.display_name,
                    icon_url=user.display_avatar.url
                )

                await channel.send(
                    content=f"{user.mention}",
                    embed=embed
                )

        return True

    async def increment_progress(
        self,
        *,
        user: discord.Member,
        achievement_id: str,
        amount: int = 1
    ) -> bool:

        ach = ACHIEVEMENTS.get(achievement_id)
        if not ach:
            raise RuntimeError(f"Achievement '{achievement_id}' not in registry")

        if ach.target is None:
            return False

        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO achievement_progress (user_id, achievement_id, progress, target)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, achievement_id)
                DO UPDATE SET progress = achievement_progress.progress + $3
                RETURNING progress
                """,
                user.id,
                achievement_id,
                amount,
                ach.target
            )

            if row["progress"] >= ach.target:
                return await self.unlock(
                    user=user,
                    achievement_id=achievement_id
                )

        return False