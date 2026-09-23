import discord
from discord.ext import commands, tasks
from typing import Optional
import asyncio
import random
import datetime
import os
from db import db
from cogs.achievements import hooks
from cogs.economy.economycommands import has_unlock, QUID_EMOJI
from config import SOCIAL_CATEGORY_ID

GIFT_ITEMS = {
    "flower": {"emoji": "🌸", "name": "flower", "price": 25,    "flavor": "a fresh bloom"},
    "cake": {"emoji": "🎂", "name": "cake", "price": 60, "flavor": "still warm"},
    "ring": {"emoji": "💍", "name": "ring", "price": 200, "flavor": "not a proposal"},
    "wine": {"emoji": "🍷", "name": "bottle of wine", "price": 80, "flavor": "a good vintage"},
    "sword": {"emoji": "⚔️",  "name": "sword", "price": 350, "flavor": "for protection"},
    "crown": {"emoji": "👑", "name": "crown", "price": 500, "flavor": "you deserve it"},
    "fish": {"emoji": "🐟", "name": "fish", "price": 10, "flavor": "still wet"},
    "letter": {"emoji": "💌", "name": "love letter", "price": 15, "flavor": "handwritten"},
    "potion": {"emoji": "🧪", "name": "mystery potion","price": 120, "flavor": "who knows whats in here"},
    "skull": {"emoji": "💀", "name": "skull", "price": 5, "flavor": "a message"},
    "telescope": {"emoji": "🔭", "name": "telescope", "price": 250, "flavor": "for seeing things far away"},
    "painting": {"emoji": "🖼️",  "name": "painting", "price": 400, "flavor": "it has your eyes"},
    "diamond": {"emoji": "💎", "name": "diamond", "price": 750, "flavor": "absurdly expensive"},
    "lantern": {"emoji": "🏮", "name": "lantern", "price": 45, "flavor": "lights the way"},
}

async def is_married(user_id: int) -> bool:
    async with db.pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT 1 FROM marriages WHERE user1=$1 OR user2=$1", user_id
        ) is not None

async def get_partner_id(user_id: int) -> int | None:
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user1, user2 FROM marriages WHERE (user1=$1 OR user2=$1) AND user1 IS NOT NULL AND user2 IS NOT NULL",
            user_id
        )
    if not row:
        return None
    return row["user2"] if row["user1"] == user_id else row["user1"]

async def is_adopted(user_id: int) -> bool:
    async with db.pool.acquire() as conn:
        return await conn.fetchval("SELECT 1 FROM adoptions WHERE child=$1", user_id) is not None

async def get_ancestors(user_id: int, limit: int = 8) -> list[int]:
    ancestors: list[int] = []
    current = user_id
    async with db.pool.acquire() as conn:
        for _ in range(limit):
            row = await conn.fetchrow("SELECT parent1, parent2 FROM adoptions WHERE child=$1", current)
            if not row:
                break
            if row["parent1"]:
                ancestors.append(row["parent1"])
            if row["parent2"]:
                ancestors.append(row["parent2"])
            current = row["parent1"]
    return ancestors

async def get_marriage_date(user_id: int) -> datetime.datetime | None:
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT married_at FROM marriages WHERE user1=$1 OR user2=$1", user_id
        )
    if not row:
        return None
    d = row["married_at"]
    return d.replace(tzinfo=datetime.timezone.utc) if d and d.tzinfo is None else d

async def bump_stat(user_id: int, column: str, amount: int = 1):
    async with db.pool.acquire() as conn:
        await conn.execute(
            f"""
            INSERT INTO social_stats (user_id, {column})
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET {column} = social_stats.{column} + $2
            """,
            user_id, amount
        )

async def get_stat(user_id: int, column: str) -> int:
    async with db.pool.acquire() as conn:
        val = await conn.fetchval(
            f"SELECT {column} FROM social_stats WHERE user_id=$1", user_id
        )
    return val or 0

async def _fire(bot, member, achievement_id: str):
    try:
        await bot.achievement_manager.unlock(user=member, achievement_id=achievement_id)
    except Exception:
        pass

async def build_family_tree(guild: discord.Guild, root_id: int, depth: int = 0, max_depth: int = 3) -> str:
    indent = "  " * depth
    member = guild.get_member(root_id)
    name = member.display_name if member else f"Unknown({root_id})"

    partner_id = await get_partner_id(root_id)
    if partner_id:
        partner = guild.get_member(partner_id)
        partner_name = partner.display_name if partner else f"Unknown({partner_id})"
        label = f"💑 {name} & {partner_name}"
    else:
        label = f"👤 {name}"

    lines = [f"{indent}{label}"]
    if depth >= max_depth:
        return "\n".join(lines)

    async with db.pool.acquire() as conn:
        children = await conn.fetch(
            "SELECT child FROM adoptions WHERE parent1=$1 OR parent2=$1", root_id
        )

    seen = set()
    for row in children:
        cid = row["child"]
        if cid in seen:
            continue
        seen.add(cid)
        lines.append(await build_family_tree(guild, cid, depth + 1, max_depth))

    return "\n".join(lines)

async def get_ai_verdict(messages: dict[int, list[str]], user1_name: str, user2_name: str) -> str:
    return "after careful deliberation, this court grants the divorce. both parties are equally insufferable. ⚖️ *BANG*"

async def get_ai_eulogy(subject_name: str, parent_name: str) -> str:
    return f"*{subject_name} was part of this family once. now they are not. such is life.* 🕯️ *they were loved. briefly.*"

JUDGE_AVATAR = "https://media.discordapp.net/attachments/1258131927760633947/1475849024459509841/vladjudge.png?ex=69a83583&is=69a6e403&hm=05e7db41480ae23a186d8c5fbaaf2ac765c33de4182446a55b81d9aa5727eb61&=&format=webp&quality=lossless&width=968&height=968"

async def end_trial(bot, trial):
    court_channel = trial["channel"]
    guild = court_channel.guild
    user1_id, user2_id = trial["users"]
    user1 = guild.get_member(user1_id)
    user2 = guild.get_member(user2_id)
    trial_role = discord.utils.get(guild.roles, name="Trialized")

    if not court_channel or not user1 or not user2 or not trial_role:
        return

    async with db.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM marriages WHERE (user1=$1 AND user2=$2) OR (user1=$2 AND user2=$1)",
            user1_id, user2_id
        )

    await hooks.on_court(bot, user1)
    await hooks.on_court(bot, user2)

    await bump_stat(user1_id, "divorces")
    await bump_stat(user2_id, "divorces")

    webhook = trial["webhook"]
    await webhook.send(
        f"divorce granted between {user1.mention} and {user2.mention}.",
        username="judge vladieu", avatar_url=JUDGE_AVATAR
    )

    await asyncio.sleep(5)
    archiving_msg = await court_channel.send("archiving case...")
    await user1.remove_roles(trial_role)
    await user2.remove_roles(trial_role)

    overwrites = court_channel.overwrites
    for target in overwrites:
        overwrites[target].read_messages = False
    await court_channel.edit(name=f"archived-{trial['case_number']}", overwrites=overwrites)
    await archiving_msg.delete()

    for m in [user1, user2]:
        await _fire(bot, m, "social.trial")
        divorces = await get_stat(m.id, "divorces")
        if divorces >= 3:
            await _fire(bot, m, "social.serial_divorcer")

    if hasattr(bot, "cogs") and "SocialCommands" in bot.cogs:
        cog = bot.cogs["SocialCommands"]
        for key in list(cog.active_trials):
            if cog.active_trials[key] == trial:
                del cog.active_trials[key]

class AdoptRequestView(discord.ui.View):
    def __init__(self, adopter: discord.Member, child: discord.Member):
        super().__init__(timeout=60)
        self.adopter = adopter
        self.child   = child

    @discord.ui.button(label="accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.child.id:
            return await interaction.response.send_message("this isn't for you", ephemeral=True)
        async with db.pool.acquire() as conn:
            partner_id = await get_partner_id(self.adopter.id)
            await conn.execute(
                "INSERT INTO adoptions (child, parent1, parent2) VALUES ($1, $2, $3)",
                self.child.id, self.adopter.id, partner_id
            )
        await bump_stat(self.adopter.id, "children")
        await interaction.response.edit_message(
            content=f"👪 {self.child.mention} was adopted by {self.adopter.mention}", view=None
        )
        self.stop()

    @discord.ui.button(label="reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.child.id:
            return await interaction.response.send_message("this isn't for you", ephemeral=True)
        await interaction.response.edit_message(content="adoption rejected", view=None)
        self.stop()


class MarriageView(discord.ui.View):
    def __init__(self, proposer: discord.Member, target: discord.Member):
        super().__init__(timeout=60)
        self.proposer = proposer
        self.target   = target

    @discord.ui.button(label="accept 💍", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("this proposal isn't for you", ephemeral=True)
        if await is_married(self.proposer.id) or await is_married(self.target.id):
            return await interaction.response.edit_message(content="❌ one of you is already married.", view=None)
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "INSERT INTO marriages (user1, user2, married_at) VALUES ($1, $2, NOW())",
                    self.proposer.id, self.target.id
                )
                await conn.execute(
                    "UPDATE user_unlocks SET marriage_pass=FALSE WHERE user_id=$1", self.proposer.id
                )
        await bump_stat(self.proposer.id, "marriages")
        await bump_stat(self.target.id,   "marriages")
        await hooks.on_marriage(interaction.client, self.proposer)
        await hooks.on_marriage(interaction.client, self.target)
        # achievements
        for m in [self.proposer, self.target]:
            await _fire(interaction.client, m, "social.married")
            marriages = await get_stat(m.id, "marriages")
            if marriages >= 3:
                await _fire(interaction.client, m, "social.married_3")
        await interaction.response.edit_message(
            content=f"💖 **{self.proposer.mention} and {self.target.mention} are now married!**", view=None
        )
        self.stop()

    @discord.ui.button(label="reject ❌", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("this proposal isn't for you", ephemeral=True)
        await _fire(interaction.client, self.proposer, "social.rejected")
        await interaction.response.edit_message(content="💔 proposal rejected", view=None)
        self.stop()


class DivorceConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=60)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    @discord.ui.button(label="yes", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, _):
        async with db.pool.acquire() as conn:
            await conn.execute("DELETE FROM marriages WHERE user1=$1 OR user2=$1", self.author.id)
            await conn.execute("DELETE FROM adoptions WHERE parent1=$1 OR parent2=$1", self.author.id)
        await interaction.response.edit_message(content="divorce finalized.", view=None)
        self.stop()

    @discord.ui.button(label="no", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(content="divorce cancelled", view=None)
        self.stop()


class AbandonConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member, child: discord.Member, bot):
        super().__init__(timeout=60)
        self.author = author
        self.child  = child
        self.bot    = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    @discord.ui.button(label="yes", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, _):
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT parent1, parent2 FROM adoptions WHERE child=$1", self.child.id)
            if not row:
                return await interaction.response.edit_message(content="❌ this child has no parents", view=None)
            if row["parent1"] == self.author.id:
                await conn.execute("DELETE FROM adoptions WHERE child=$1", self.child.id)
            elif row["parent2"] == self.author.id:
                await conn.execute("UPDATE adoptions SET parent2=NULL WHERE child=$1", self.child.id)
            else:
                return await interaction.response.edit_message(content="❌ you are not this child's parent", view=None)

        eulogy = await get_ai_eulogy(self.child.display_name, self.author.display_name)
        await interaction.response.edit_message(
            content=f"💔 {self.author.mention} abandoned {self.child.mention}\n\n{eulogy}", view=None
        )
        self.stop()

    @discord.ui.button(label="no", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(content="abandon cancelled", view=None)
        self.stop()


class GiftCatalogueView(discord.ui.View):
    def __init__(self, bot, sender: discord.Member, receiver: discord.Member, message: str | None):
        super().__init__(timeout=60)
        self.bot      = bot
        self.sender   = sender
        self.receiver = receiver
        self.message  = message
        self.items    = list(GIFT_ITEMS.items())
        self.page     = 0
        self.per_page = 5
        self._build()

    def _build(self):
        self.clear_items()
        start = self.page * self.per_page
        chunk = self.items[start:start + self.per_page]
        for item_id, item in chunk:
            self.add_item(GiftButton(item_id, item, self.sender, self.receiver, self.message, self.bot))
        total = (len(self.items) - 1) // self.per_page
        prev = discord.ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=self.page == 0)
        next_ = discord.ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=self.page >= total)

        async def prev_cb(interaction: discord.Interaction):
            if interaction.user.id != self.sender.id:
                return await interaction.response.send_message("not your catalogue", ephemeral=True)
            self.page -= 1
            self._build()
            await interaction.response.edit_message(embed=self._embed(), view=self)

        async def next_cb(interaction: discord.Interaction):
            if interaction.user.id != self.sender.id:
                return await interaction.response.send_message("not your catalogue", ephemeral=True)
            self.page += 1
            self._build()
            await interaction.response.edit_message(embed=self._embed(), view=self)

        prev.callback = prev_cb
        next_.callback = next_cb
        self.add_item(prev)
        self.add_item(next_)

    def _embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🎁 gift catalogue for {self.receiver.display_name}",
            color=discord.Color.pink()
        )
        start = self.page * self.per_page
        chunk = self.items[start:start + self.per_page]
        for _, item in chunk:
            embed.add_field(
                name=f"{item['emoji']} {item['name']}  -  {item['price']} {QUID_EMOJI}",
                value=item["flavor"],
                inline=False
            )
        total = (len(self.items) - 1) // self.per_page + 1
        embed.set_footer(text=f"page {self.page + 1}/{total} • click to send")
        return embed


class GiftButton(discord.ui.Button):
    def __init__(self, item_id, item, sender, receiver, message, bot):
        super().__init__(
            label=f"{item['emoji']} {item['name']} ({item['price']})",
            style=discord.ButtonStyle.primary
        )
        self.item_id = item_id
        self.item = item
        self.sender = sender
        self.receiver = receiver
        self.message = message
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.sender.id:
            return await interaction.response.send_message("not your gift to give", ephemeral=True)

        async with db.pool.acquire() as conn:
            wallet = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", self.sender.id) or 0
            if wallet < self.item["price"]:
                return await interaction.response.send_message(
                    f"❌ you need **{self.item['price']}** {QUID_EMOJI}. you have **{wallet}**.", ephemeral=True
                )
            await conn.execute("UPDATE economy SET quid=quid-$1 WHERE user_id=$2", self.item["price"], self.sender.id)
            await conn.execute(
                "INSERT INTO social_gifts (sender_id, receiver_id, item, message) VALUES ($1,$2,$3,$4)",
                self.sender.id, self.receiver.id, self.item_id, self.message
            )

        await bump_stat(self.sender.id,   "gifts_given")
        await bump_stat(self.receiver.id, "gifts_received")

        msg_line = f"\n*\"{self.message}\"*" if self.message else ""
        embed = discord.Embed(
            title=f"{self.item['emoji']} gift sent!",
            description=(
                f"**{self.sender.display_name}** sent {self.receiver.mention} a **{self.item['name']}**!"
                f"{msg_line}\n\n{self.item['flavor']}"
            ),
            color=discord.Color.pink()
        )
        await interaction.response.edit_message(embed=embed, view=None)

        given = await get_stat(self.sender.id, "gifts_given")
        if given >= 1:   await _fire(self.bot, self.sender, "social.first_gift")
        if given >= 10:  await _fire(self.bot, self.sender, "social.generous")
        if self.item_id == "skull":
            await _fire(self.bot, self.sender, "social.sent_skull")
        if self.item_id == "diamond":
            await _fire(self.bot, self.sender, "social.sent_diamond")

        received = await get_stat(self.receiver.id, "gifts_received")
        if received >= 1:  await _fire(self.bot, self.receiver, "social.first_gift_received")

class FamilyProfileView(discord.ui.View):
    def __init__(self, bot, member: discord.Member):
        super().__init__(timeout=30)
        self.bot    = bot
        self.member = member

    @discord.ui.button(label="🌳 expand tree", style=discord.ButtonStyle.secondary)
    async def expand(self, interaction: discord.Interaction, _):
        tree = await build_family_tree(interaction.guild, self.member.id, max_depth=4)
        if len(tree) > 1800:
            tree = tree[:1800] + "\n*...tree too large to display fully*"
        await interaction.response.send_message(f"```\n{tree}\n```", ephemeral=True)

class FeudChallengeView(discord.ui.View):
    def __init__(self, challenger: discord.Member, target: discord.Member):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.target     = target
        self.accepted   = False

    @discord.ui.button(label="⚔️ accept", style=discord.ButtonStyle.danger)
    async def accept(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("not your fight", ephemeral=True)
        self.accepted = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="🏳️ decline", style=discord.ButtonStyle.secondary)
    async def decline(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("not your fight", ephemeral=True)
        self.stop()
        await interaction.response.edit_message(content="feud declined.", view=None)


class FeudMoveView(discord.ui.View):
    def __init__(self, player: discord.Member):
        super().__init__(timeout=15)
        self.player = player
        self.choice: str | None = None

    async def _pick(self, interaction: discord.Interaction, move: str):
        if interaction.user.id != self.player.id:
            return await interaction.response.send_message("not your turn", ephemeral=True)
        self.choice = move
        self.stop()
        await interaction.response.edit_message(content=f"you chose...", view=None)

    @discord.ui.button(label="⚔️ strike", style=discord.ButtonStyle.danger)
    async def strike(self, i, _): await self._pick(i, "strike")

    @discord.ui.button(label="🛡️ dodge", style=discord.ButtonStyle.primary)
    async def dodge(self, i, _): await self._pick(i, "dodge")

    @discord.ui.button(label="😤 taunt", style=discord.ButtonStyle.secondary)
    async def taunt(self, i, _): await self._pick(i, "taunt")

class RepConfirmView(discord.ui.View):
    def __init__(self, giver: discord.Member, receiver: discord.Member, bot):
        super().__init__(timeout=30)
        self.giver    = giver
        self.receiver = receiver
        self.bot      = bot

    @discord.ui.button(label="✅ confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.giver.id:
            return await interaction.response.send_message("not yours", ephemeral=True)

        now = datetime.datetime.now(datetime.timezone.utc)
        async with db.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT given_at FROM social_rep WHERE giver_id=$1 AND receiver_id=$2",
                self.giver.id, self.receiver.id
            )
            if existing:
                last = existing["given_at"].replace(tzinfo=datetime.timezone.utc) if existing["given_at"].tzinfo is None else existing["given_at"]
                if (now - last).total_seconds() < 86400:
                    ts = int((last + datetime.timedelta(seconds=86400)).timestamp())
                    return await interaction.response.edit_message(
                        content=f"you already repped them recently. try again <t:{ts}:R>.", view=None
                    )
                await conn.execute(
                    "UPDATE social_rep SET given_at=$1 WHERE giver_id=$2 AND receiver_id=$3",
                    now, self.giver.id, self.receiver.id
                )
            else:
                await conn.execute(
                    "INSERT INTO social_rep (giver_id, receiver_id, given_at) VALUES ($1,$2,$3)",
                    self.giver.id, self.receiver.id, now
                )

            await conn.execute(
                """
                INSERT INTO social_rep_totals (user_id, rep) VALUES ($1, 1)
                ON CONFLICT (user_id) DO UPDATE SET rep = social_rep_totals.rep + 1
                """,
                self.receiver.id
            )
            total = await conn.fetchval("SELECT rep FROM social_rep_totals WHERE user_id=$1", self.receiver.id) or 1

        await bump_stat(self.giver.id,    "rep_given")
        await bump_stat(self.receiver.id, "rep_received")

        await interaction.response.edit_message(
            content=f"✅ gave rep to **{self.receiver.display_name}**. their total: **{total}** ⭐", view=None
        )

        given_total = await get_stat(self.giver.id, "rep_given")
        if given_total >= 1:  await _fire(self.bot, self.giver,    "social.first_rep_given")
        if given_total >= 25: await _fire(self.bot, self.giver,    "social.rep_philanthropist")
        if total >= 10:  await _fire(self.bot, self.receiver, "social.rep_10")
        if total >= 50:  await _fire(self.bot, self.receiver, "social.rep_50")
        if total >= 100: await _fire(self.bot, self.receiver, "social.rep_100")

    @discord.ui.button(label="cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(content="cancelled.", view=None)
        self.stop()

class WillConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member, beneficiary: discord.Member, amount: int, message: str | None, bot):
        super().__init__(timeout=30)
        self.author      = author
        self.beneficiary = beneficiary
        self.amount      = amount
        self.message     = message
        self.bot         = bot

    @discord.ui.button(label="✍️ sign", style=discord.ButtonStyle.success)
    async def sign(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("not yours to sign", ephemeral=True)
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO social_wills (user_id, beneficiary, amount, message, updated_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (user_id) DO UPDATE
                    SET beneficiary=EXCLUDED.beneficiary, amount=EXCLUDED.amount,
                        message=EXCLUDED.message, updated_at=NOW()
                """,
                self.author.id, self.beneficiary.id, self.amount, self.message
            )
        await interaction.response.edit_message(
            content=f"📜 will written. **{self.beneficiary.display_name}** will receive **{self.amount:,}** {QUID_EMOJI}.", view=None
        )
        await _fire(self.bot, self.author, "social.wrote_will")
        self.stop()

    @discord.ui.button(label="cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(content="will cancelled.", view=None)
        self.stop()

class SocialCommands(commands.Cog):
    def __init__(self, bot):
        self.bot           = bot
        self.active_trials = {}
        self.active_feuds  = set()

    @commands.command(name="marry", help="propose to someone", usage="!marry @user")
    async def marry(self, ctx, member: discord.Member):
        if member.bot or member.id == ctx.author.id:
            return await ctx.send("no.")
        if not await has_unlock(ctx.author.id, "marriage_pass"):
            return await ctx.send("you need an engagement ring. buy one with `!shop`.")
        if await is_married(ctx.author.id) or await is_married(member.id):
            return await ctx.send("someone is already married.")
        embed = discord.Embed(
            title="💍 marriage proposal",
            description=f"{ctx.author.mention} is proposing to {member.mention}",
            color=discord.Color.pink()
        )
        await ctx.send(content=member.mention, embed=embed, view=MarriageView(ctx.author, member))

    @commands.command(name="spouse", help="see who you're married to", usage="!spouse [user]")
    async def spouse(self, ctx, member: Optional[discord.Member] = None):
        target = member or ctx.author
        if not await is_married(target.id):
            return await ctx.send("this person is not married.")
        partner_id = await get_partner_id(target.id)
        if partner_id is None:
            return await ctx.send("marriage data is corrupted.")
        partner = ctx.guild.get_member(partner_id)
        if not partner:
            try:
                partner = await ctx.guild.fetch_member(partner_id)
            except discord.NotFound:
                return await ctx.send("spouse not found (left the server?)")

        married_at = await get_marriage_date(target.id)
        ann_line = ""
        if married_at:
            days = (datetime.datetime.now(datetime.timezone.utc) - married_at).days
            ann_line = f"\n*married {days} day{'s' if days != 1 else ''} ago*"

        embed = discord.Embed(
            title="💖 marriage",
            description=f"**{target.display_name}** is married to **{partner.display_name}**{ann_line}",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @commands.command(name="anniversary", help="check your marriage anniversary", usage="!anniversary")
    async def anniversary(self, ctx):
        if not await is_married(ctx.author.id):
            return await ctx.send("you're not married.")
        married_at = await get_marriage_date(ctx.author.id)
        if not married_at:
            return await ctx.send("no marriage date on record.")
        now   = datetime.datetime.now(datetime.timezone.utc)
        days  = (now - married_at).days
        years = days // 365
        next_ann = married_at.replace(year=married_at.year + years + 1)
        ts = int(next_ann.timestamp())
        embed = discord.Embed(
            title="🎉 anniversary",
            description=(
                f"you've been married for **{days}** days ({years} year{'s' if years != 1 else ''}).\n"
                f"next anniversary: <t:{ts}:D>"
            ),
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
        if years >= 1:
            await _fire(self.bot, ctx.author, "social.anniversary_1yr")

    @commands.command(name="divorce", help="file for divorce in court", usage="!divorce @user")
    async def divorce(self, ctx, partner: discord.Member):
        if partner.bot or partner.id == ctx.author.id:
            return await ctx.send("no.")
        if not await is_married(ctx.author.id):
            return await ctx.send("you aren't married.")

        guild = ctx.guild
        trial_role = discord.utils.get(guild.roles, name="Trialized")
        if not trial_role:
            trial_role = await guild.create_role(name="Trialized", colour=discord.Colour.gold())
        await ctx.author.add_roles(trial_role)
        await partner.add_roles(trial_role)

        all_nums = []
        for c in guild.channels:
            if c.name.startswith("case-") or c.name.startswith("archived-"):
                try:
                    all_nums.append(int(c.name.split("-")[1]))
                except ValueError:
                    pass
        case_number = max(all_nums, default=0) + 1

        category = guild.get_channel(SOCIAL_CATEGORY_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author:         discord.PermissionOverwrite(read_messages=True, send_messages=True),
            partner:            discord.PermissionOverwrite(read_messages=True, send_messages=True),
            self.bot.user:      discord.PermissionOverwrite(read_messages=True)
        }
        court_channel = await guild.create_text_channel(
            name=f"case-{case_number}", overwrites=overwrites, category=category
        )
        judge_webhook = await court_channel.create_webhook(name="judge vladieu")

        await judge_webhook.send(
            content=(
                f"💔 {ctx.author.mention} has filed for divorce against {partner.mention}.\n"
                "welcome to the court. please submit your opening statements.\n"
                "after both parties have spoken, you will each have one final argument. "
                "judge vladieu will then deliver a verdict."
            ),
            username="judge vladieu", avatar_url=JUDGE_AVATAR
        )

        self.active_trials[(ctx.author.id, partner.id)] = {
            "channel":    court_channel,
            "users":      [ctx.author.id, partner.id],
            "user_names": {ctx.author.id: ctx.author.display_name, partner.id: partner.display_name},
            "messages":   {},
            "phase":      "opening",
            "webhook":    judge_webhook,
            "case_number": case_number
        }

    @commands.command(name="adopt", help="adopt someone as your child", usage="!adopt @user")
    async def adopt(self, ctx, member: discord.Member):
        if member.bot or member.id == ctx.author.id:
            return await ctx.send("no.")
        async with db.pool.acquire() as conn:
            exists = await conn.fetchval(
                "SELECT 1 FROM adoptions WHERE child=$1 AND (parent1 IS NOT NULL OR parent2 IS NOT NULL)", member.id
            )
        if exists:
            return await ctx.send("this person already has parents.")
        embed = discord.Embed(
            title="👪 adoption request",
            description=f"{ctx.author.mention} wants to adopt {member.mention}",
            color=discord.Color.blurple()
        )
        await ctx.send(content=member.mention, embed=embed, view=AdoptRequestView(ctx.author, member))
        await _fire(self.bot, ctx.author, "social.adopted_someone")

    @commands.command(name="abandon", help="abandon your adopted child", usage="!abandon @user")
    async def abandon(self, ctx, member: discord.Member):
        async with db.pool.acquire() as conn:
            exists = await conn.fetchval("SELECT 1 FROM adoptions WHERE child=$1", member.id)
        if not exists:
            return await ctx.send("this person has no parents.")
        embed = discord.Embed(
            title="💔 abandon child",
            description=f"are you sure you want to abandon **{member.display_name}**?",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, view=AbandonConfirmView(ctx.author, member, self.bot))

    @commands.command(name="parents", help="see who your parents are", usage="!parents [user]")
    async def parents(self, ctx, member: Optional[discord.Member] = None):
        target = member or ctx.author
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT parent1, parent2 FROM adoptions WHERE child=$1", target.id)
        if not row:
            return await ctx.send(f"**{target.display_name}** has no parents on record.")
        p1 = ctx.guild.get_member(row["parent1"]) if row["parent1"] else None
        p2 = ctx.guild.get_member(row["parent2"]) if row["parent2"] else None
        parents_str = " and ".join(
            m.display_name for m in [p1, p2] if m
        ) or "unknown"
        await ctx.send(f"👪 **{target.display_name}**'s parents: **{parents_str}**")

    @commands.command(name="children", help="see your adopted children", usage="!children [user]")
    async def children(self, ctx, member: Optional[discord.Member] = None):
        target = member or ctx.author
        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT child FROM adoptions WHERE parent1=$1 OR parent2=$1", target.id)
        if not rows:
            return await ctx.send(f"**{target.display_name}** has no children.")
        names = []
        for r in rows:
            m = ctx.guild.get_member(r["child"])
            names.append(m.display_name if m else f"<{r['child']}>")
        embed = discord.Embed(
            title=f"👪 {target.display_name}'s children",
            description="\n".join(f"• {n}" for n in names),
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="family", help="view your family", usage="!family [user]")
    async def family(self, ctx, member: Optional[discord.Member] = None):
        target = member or ctx.author
        async with db.pool.acquire() as conn:
            current = target.id
            for _ in range(10):
                row = await conn.fetchrow("SELECT parent1 FROM adoptions WHERE child=$1", current)
                if not row or not row["parent1"]:
                    break
                current = row["parent1"]
        root_id = current

        tree = await build_family_tree(ctx.guild, root_id, max_depth=3)
        if len(tree) > 1800:
            tree = tree[:1800] + "\n*...tree too large*"
        embed = discord.Embed(
            title=f"🌳 family tree",
            description=f"```\n{tree}\n```",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, view=FamilyProfileView(self.bot, target))

    @commands.command(name="gift", help="send someone a gift", usage="!gift @user [message]")
    async def gift(self, ctx, member: discord.Member, *, message: Optional[str] = None):
        if member.bot or member.id == ctx.author.id:
            return await ctx.send("no.")
        view  = GiftCatalogueView(self.bot, ctx.author, member, message)
        await ctx.send(embed=view._embed(), view=view)

    @commands.command(name="gifts", help="see your received gifts", usage="!gifts [user]")
    async def gifts(self, ctx, member: Optional[discord.Member] = None):
        target = member or ctx.author
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT sender_id, item, message, sent_at FROM social_gifts WHERE receiver_id=$1 ORDER BY sent_at DESC LIMIT 10",
                target.id
            )
        if not rows:
            return await ctx.send(f"**{target.display_name}** hasn't received any gifts.")
        embed = discord.Embed(title=f"🎁 {target.display_name}'s gifts", color=discord.Color.pink())
        for row in rows:
            sender  = ctx.guild.get_member(row["sender_id"])
            name    = sender.display_name if sender else f"<{row['sender_id']}>"
            item    = GIFT_ITEMS.get(row["item"], {"emoji": "📦", "name": row["item"]})
            ts      = int(row["sent_at"].timestamp())
            val     = f"from **{name}** <t:{ts}:R>"
            if row["message"]:
                val += f"\n*\"{row['message']}\"*"
            embed.add_field(name=f"{item['emoji']} {item['name']}", value=val, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="rep", aliases=["giverep"], help="give someone reputation", usage="!rep @user")
    async def rep(self, ctx, member: discord.Member):
        if member.bot or member.id == ctx.author.id:
            return await ctx.send("no.")
        async with db.pool.acquire() as conn:
            total = await conn.fetchval("SELECT rep FROM social_rep_totals WHERE user_id=$1", member.id) or 0
        embed = discord.Embed(
            title="⭐ give reputation",
            description=f"give rep to **{member.display_name}**? they currently have **{total}** ⭐",
            color=discord.Color.yellow()
        )
        await ctx.send(embed=embed, view=RepConfirmView(ctx.author, member, self.bot))

    @commands.command(name="reps", aliases=["reptop", "reputation"], help="view rep", usage="!reps [user]")
    async def reputation(self, ctx, member: Optional[discord.Member] = None):
        if member:
            async with db.pool.acquire() as conn:
                total = await conn.fetchval("SELECT rep FROM social_rep_totals WHERE user_id=$1", member.id) or 0
            return await ctx.send(f"⭐ **{member.display_name}** has **{total}** reputation.")
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT user_id, rep FROM social_rep_totals ORDER BY rep DESC LIMIT 10"
            )
        if not rows:
            return await ctx.send("no reputation data yet.")
        embed = discord.Embed(title="⭐ reputation leaderboard", color=discord.Color.yellow())
        medals = ["🥇", "🥈", "🥉"]
        for i, row in enumerate(rows):
            m = ctx.guild.get_member(row["user_id"])
            name = m.display_name if m else f"<{row['user_id']}>"
            prefix = medals[i] if i < 3 else f"**{i+1}.**"
            embed.add_field(name=f"{prefix} {name}", value=f"**{row['rep']}** ⭐", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="will", help="write a will", usage="!will @user <amount> [message]")
    async def will(self, ctx, beneficiary: discord.Member, amount: int, *, message: Optional[str] = None):
        if beneficiary.bot or beneficiary.id == ctx.author.id:
            return await ctx.send("no.")
        if amount <= 0:
            return await ctx.send("amount must be positive.")
        async with db.pool.acquire() as conn:
            wallet = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0
        if amount > wallet:
            return await ctx.send(f"you only have **{wallet:,}** {QUID_EMOJI}.")

        embed = discord.Embed(
            title="📜 write a will",
            description=(
                f"**beneficiary:** {beneficiary.mention}\n"
                f"**amount:** {amount:,} {QUID_EMOJI}\n"
                + (f"**message:** *\"{message}\"*" if message else "")
                + "\n\n*this will be triggered manually by an admin or automatically on inactivity.*"
            ),
            color=discord.Color.greyple()
        )
        await ctx.send(embed=embed, view=WillConfirmView(ctx.author, beneficiary, amount, message, self.bot))

    @commands.command(name="mywill", help="view your current will", usage="!mywill")
    async def mywill(self, ctx):
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT beneficiary, amount, message, updated_at FROM social_wills WHERE user_id=$1", ctx.author.id)
        if not row:
            return await ctx.send("you haven't written a will. use `!will @user <amount>`.")
        ben = ctx.guild.get_member(row["beneficiary"])
        ben_name = ben.display_name if ben else f"<{row['beneficiary']}>"
        ts = int(row["updated_at"].timestamp())
        embed = discord.Embed(title="📜 your will", color=discord.Color.greyple())
        embed.add_field(name="beneficiary", value=ben_name, inline=True)
        embed.add_field(name="amount", value=f"{row['amount']:,} {QUID_EMOJI}", inline=True)
        embed.add_field(name="updated", value=f"<t:{ts}:R>", inline=True)
        if row["message"]:
            embed.add_field(name="message", value=f"*\"{row['message']}\"*", inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        trial = None
        for (u1, u2), state in self.active_trials.items():
            if message.author.id in (u1, u2) and message.channel == state["channel"]:
                trial = state
                break
        if not trial:
            return

        trial["messages"].setdefault(message.author.id, []).append(message.content)

        if trial["phase"] == "opening":
            if all(uid in trial["messages"] for uid in trial["users"]):
                trial["phase"] = "final"
                await trial["webhook"].send(
                    content="all opening statements received. proceed to your final arguments.",
                    username="judge vladieu", avatar_url=JUDGE_AVATAR
                )

        elif trial["phase"] == "final":
            if all(len(trial["messages"].get(uid, [])) >= 2 for uid in trial["users"]):
                trial["phase"] = "verdict"
                await trial["webhook"].send(
                    content="⚖️ *the judge reviews the evidence...*",
                    username="judge vladieu", avatar_url=JUDGE_AVATAR
                )
                u1_id, u2_id = trial["users"]
                user_names   = trial.get("user_names", {})
                verdict = await get_ai_verdict(
                    trial["messages"],
                    user_names.get(u1_id, str(u1_id)),
                    user_names.get(u2_id, str(u2_id))
                )
                await trial["webhook"].send(content=verdict, username="judge vladieu", avatar_url=JUDGE_AVATAR)
                await asyncio.sleep(3)
                await end_trial(self.bot, trial)


async def setup(bot):
    await bot.add_cog(SocialCommands(bot))