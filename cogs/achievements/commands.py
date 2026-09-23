import os
import discord
from discord.ext import commands
from collections import defaultdict

from db import db
from .registry import ACHIEVEMENTS, BONUS_ACHIEVEMENT_IDS
from cogs.achievements.manager import AchievementManager

AIRole = int(os.getenv("AIRole"))

def progress_bar(progress: int, target: int, size: int = 10) -> str:
    if target <= 0:
        return ""
    filled = int((progress / target) * size)
    filled = max(0, min(size, filled))
    return "▰" * filled + "▱" * (size - filled)

class AchievementCategoryView(discord.ui.View):
    def __init__(self, *, ctx, user, unlocked, progress_map):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.user = user
        self.unlocked = unlocked
        self.progress_map = progress_map

        self.page = 1
        self.total_pages = 1
        self.lines = []
        self.mode = "menu"
        self.current_category = None
        self.per_page = 15

        categories = sorted({a.category for a in ACHIEVEMENTS.values()})

        self.select.options = [
            discord.SelectOption(label=cat, value=cat)
            for cat in categories
        ]

    def update_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.label == "◀":
                    item.disabled = self.page <= 1
                elif item.label == "▶":
                    item.disabled = self.page >= self.total_pages

    def build_missing_lines(self):
        lines = []
        for ach in ACHIEVEMENTS.values():
            if ach.id in self.unlocked:
                continue
            if ach.id in BONUS_ACHIEVEMENT_IDS:
                continue
            if ach.hidden:
                hint = f"\n*hint: {ach.hint}*" if ach.hint else ""
                lines.append(f"❓ **hidden achievement**\ndiscover a secret{hint}")
                continue
            if ach.target:
                progress, target = self.progress_map.get(ach.id, (0, ach.target))
                bar = progress_bar(progress, target)
                lines.append(
                    f"🔒 **{ach.name}**\n"
                    f"`{bar}` **{progress}/{target}**\n"
                    f"{ach.description}"
                )
            else:
                lines.append(f"🔒 **{ach.name}**\n{ach.description}")
        return lines

    async def generate_embed(self):
        start = (self.page - 1) * self.per_page
        end   = start + self.per_page
        chunk = self.lines[start:end]

        normal_ids = [a for a in ACHIEVEMENTS if a not in BONUS_ACHIEVEMENT_IDS]
        total = len(normal_ids)
        bonus_owned = len([a for a in self.unlocked if a in BONUS_ACHIEVEMENT_IDS])
        normal_owned = len([a for a in self.unlocked if a not in BONUS_ACHIEVEMENT_IDS])
        display_unlocked = normal_owned + bonus_owned
        display_total = total + bonus_owned
        percent = (display_unlocked / total) * 100 if total else 0

        if self.mode == "missing":
            title = "🔒 missing achievements"
            color = discord.Color.dark_grey()
        else:
            title = f"🏆 {self.user.display_name}'s achievements"
            color = discord.Color.gold()

        embed = discord.Embed(
            title=title,
            description=(
                f"**progress:** {display_unlocked} / {display_total} "
                f"(**{percent:.0f}%**)\n\n" +
                ("\n\n".join(chunk) if chunk else "*nothing here*")
            ),
            color=color
        )

        footer = f"page {self.page}/{self.total_pages}"
        if self.mode == "category":
            footer += f" • category: {self.current_category}"
        embed.set_footer(text=footer)
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("this menu isnt for you lil bro", ephemeral=True)
            return False
        return True

    @discord.ui.select(placeholder="choose a category…", min_values=1, max_values=1, options=[])
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = select.values[0]
        self.mode = "category"
        self.current_category = category

        lines = []
        for ach in ACHIEVEMENTS.values():
            if ach.category != category:
                continue
            if ach.id in BONUS_ACHIEVEMENT_IDS and ach.id not in self.unlocked:
                continue
            if ach.hidden and ach.id not in self.unlocked:
                hint = f"\n*hint: {ach.hint}*" if ach.hint else ""
                lines.append(f"❓ **hidden achievement**\ndiscover a secret{hint}")
                continue
            if ach.id in self.unlocked:
                lines.append(f"✅ **{ach.name}**\n{ach.description}")
            else:
                if ach.target:
                    progress, target = self.progress_map.get(ach.id, (0, ach.target))
                    bar = progress_bar(progress, target)
                    lines.append(
                        f"🔒 **{ach.name}**\n"
                        f"`{bar}` **{progress}/{target}**\n"
                        f"{ach.description}"
                    )
                else:
                    lines.append(f"🔒 **{ach.name}**\n{ach.description}")

        if not lines:
            lines.append("*no achievements in this category*")

        self.lines       = lines
        self.page        = 1
        self.total_pages = max(1, (len(lines) + self.per_page - 1) // self.per_page)

        embed = await self.generate_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="missing", style=discord.ButtonStyle.secondary, emoji="🔒")
    async def missing_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode             = "missing"
        self.current_category = None
        self.lines            = self.build_missing_lines()
        self.page             = 1
        self.total_pages      = max(1, (len(self.lines) + self.per_page - 1) // self.per_page)

        embed = await self.generate_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.success)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.mode not in ("missing", "category"):
            return await interaction.response.defer()
        if self.page > 1:
            self.page -= 1
            embed = await self.generate_embed()
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="▶", style=discord.ButtonStyle.success)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.mode not in ("missing", "category"):
            return await interaction.response.defer()
        if self.page < self.total_pages:
            self.page += 1
            embed = await self.generate_embed()
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()


class AchTopView(discord.ui.View):
    def __init__(self, *, ctx, rows: list, total_achievements: int):
        super().__init__(timeout=120)
        self.ctx                = ctx
        self.rows               = rows
        self.total_achievements = total_achievements
        self.page               = 0
        self.per_page           = 5
        self.total_pages        = max(1, (len(rows) + self.per_page - 1) // self.per_page)
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page >= self.total_pages - 1

    def build_embed(self) -> discord.Embed:
        embed  = discord.Embed(title="🏆 achievement leaderboard", color=discord.Color.gold())
        start  = self.page * self.per_page
        chunk  = self.rows[start:start + self.per_page]
        medals = {0: "<:diamondvlad:1402318150028234752>", 1: "<:goldvlad:1402318157552685159>", 2: "<:silvervlad:1402318161461907597>"}
        lines  = []
        for i, (user_id, count) in enumerate(chunk):
            rank   = start + i
            medal  = medals.get(rank, f"`#{rank + 1}`")
            pct    = (count / self.total_achievements * 100) if self.total_achievements else 0
            member = self.ctx.guild.get_member(user_id)
            name   = member.display_name if member else f"<@{user_id}>"
            bar    = progress_bar(count, self.total_achievements, size=12)
            lines.append(f"{medal} **{name}**\n`{bar}` {count}/{self.total_achievements} ({pct:.0f}%)")
        embed.description = "\n\n".join(lines) if lines else "*no data*"
        embed.set_footer(text=f"page {self.page + 1}/{self.total_pages}")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("not your menu", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀", style=discord.ButtonStyle.success)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.success)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class AchievementCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="achievements",
        aliases=["ach", "achieve"],
        help="view your achievements"
    )
    async def achievements(self, ctx, member: discord.Member | None = None):
        user = member or ctx.author

        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT achievement_id FROM user_achievements WHERE user_id = $1",
                user.id
            )
            progress_rows = await conn.fetch(
                "SELECT achievement_id, progress, target FROM achievement_progress WHERE user_id = $1",
                user.id
            )
            progress_map = {
                r["achievement_id"]: (r["progress"], r["target"])
                for r in progress_rows
            }

        unlocked       = {r["achievement_id"] for r in rows}
        bonus_ids      = BONUS_ACHIEVEMENT_IDS
        normal_total   = len([a for a in ACHIEVEMENTS if a not in bonus_ids])
        bonus_owned    = len([a for a in unlocked if a in bonus_ids])
        normal_owned   = len([a for a in unlocked if a not in bonus_ids])
        total          = normal_total
        unlocked_count = normal_owned

        display_unlocked = unlocked_count + bonus_owned
        display_total    = normal_total + bonus_owned 
        percent          = (display_unlocked / normal_total) * 100 if normal_total else 0

        embed = discord.Embed(
            title=f"🏆 {user.display_name}'s achievements",
            description=(
                f"**progress:** {display_unlocked} / {display_total} "
                f"(**{percent:.0f}%**)\n\n"
                "✅ unlocked  🔒 locked  ❓ hidden\n\n"
                "use the menu below to browse achievement categories"
            ),
            color=discord.Color.gold()
        )

        view = AchievementCategoryView(
            ctx=ctx, user=user, unlocked=unlocked, progress_map=progress_map
        )
        await ctx.send(embed=embed, view=view)

    @commands.command(
        name="achtop",
        aliases=["achlb", "achievetop"],
        help="achievement leaderboard",
        usage="!achtop"
    )
    async def achtop(self, ctx):
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, COUNT(*) AS count
                FROM user_achievements
                GROUP BY user_id
                ORDER BY count DESC
                """
            )

        if not rows:
            return await ctx.send("no achievement data yet.")

        data = [(r["user_id"], r["count"]) for r in rows]
        normal_total = len([a for a in ACHIEVEMENTS if a not in BONUS_ACHIEVEMENT_IDS])
        view = AchTopView(ctx=ctx, rows=data, total_achievements=normal_total)
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(
        name="giveach",
        help="give a user an achievement or ALL",
        usage="!giveach <user> <ach.id|all>"
    )
    @commands.has_role(AIRole)
    async def giveach(self, ctx, member: discord.Member, achievement_id: str):
        achievement_id = achievement_id.strip()
        mgr = AchievementManager(self.bot)

        if achievement_id.lower() == "all":
            given = 0
            for ach_id in ACHIEVEMENTS.keys():
                unlocked = await mgr.unlock(user=member, achievement_id=ach_id)
                if unlocked:
                    given += 1
            return await ctx.send(f"✅ gave **{given} achievements** to {member.display_name}")

        if achievement_id not in ACHIEVEMENTS:
            return await ctx.send(f"❌ achievement `{achievement_id}` does not exist")

        unlocked = await mgr.unlock(user=member, achievement_id=achievement_id)
        if not unlocked:
            return await ctx.send(f"⚠️ {member.display_name} already has `{achievement_id}`")
        await ctx.send(f"✅ gave **{achievement_id}** to {member.display_name}")

    @commands.command(
        name="removeach",
        help="remove an achievement or ALL",
        usage="!removeach <user> <ach.id|all>"
    )
    @commands.has_role(AIRole)
    async def removeach(self, ctx, member: discord.Member, achievement_id: str):
        achievement_id = achievement_id.strip()

        async with db.pool.acquire() as conn:
            if achievement_id.lower() == "all":
                await conn.execute("DELETE FROM user_achievements WHERE user_id=$1", member.id)
                return await ctx.send(f"🧹 wiped ALL achievements from {member.display_name}")

            if achievement_id not in ACHIEVEMENTS:
                return await ctx.send(f"❌ achievement `{achievement_id}` does not exist")

            deleted = await conn.execute(
                "DELETE FROM user_achievements WHERE user_id=$1 AND achievement_id=$2",
                member.id, achievement_id
            )

        if deleted.endswith("0"):
            return await ctx.send(f"⚠️ {member.display_name} did not have `{achievement_id}`")
        await ctx.send(f"❌ removed **{achievement_id}** from {member.display_name}")


async def setup(bot):
    from .manager import AchievementManager

    mgr = AchievementManager(bot)
    await mgr.sync_registry()

    await bot.add_cog(AchievementCommands(bot))