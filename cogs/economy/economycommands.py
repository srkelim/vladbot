# CHANGE WORK COOLDOWN BACK TO 1800
import os
import discord
from discord.ext import commands, tasks
import typing
import random
import time
import datetime
import asyncio
from cogs.achievements import hooks
from cogs.finance.financecommands import get_stock_price

from config import JAIL_ROLE_ID, POLICE_JAIL_ROLE_ID, JAIL_DAYS, QUID_EMOJI, XP_PER_QUID, MINNEAPOLIS_CHANNEL, MINNEAPOLIS_ROLE, \
    SIGWATER_CHANNEL, SIGWATER_ROLE, EVIL_EMOJI, HEAVEN_ROLE, ICY_PEAKS_ROLE, ICY_PEAKS_CHANNEL, KEY_CHANNEL, TAX_COLLECTOR_CHANNEL, \
    TAX_COLLECTOR_ROLE, HOUSEOFVLADS_ROLE

from db import db

AIRole = int(os.getenv("AIRole"))

JAIL_CHANNEL = 1456373077616361522

PAGE_NAMES = ["items", "vacations", "fishing", "secret"]
BONE_EMBLEM_ID = "bone_emblem"
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
ITEMS_PER_PAGE = 8

MILESTONES = {
    3: 250,
    7: 750,
    14: 5000,
    30: 15000,
}

SHOP_ITEMS = {
    "quidburn": {
        "type": "refund",
        "name": "1 quid",
        "price": 2,
        "currency": "quid",
        "refund": 1,
        "description": "buy 1 quid for 2 quid 🔥"
    },
    "crime": {
        "type": "unlock",
        "name": "crime pass",
        "price": 300,
        "currency": "quid",
        "unlock_key": "crime_pass",
        "description": "access to crime commands",
        "inspect_description": (
            "an underground clearance pass recognized by the land's worst people\n\n"
            "unlocks access to illegal activities\n"
            "purchased from the shop"
        ),
        "emoji": "🚓",
    },
    "ring": {
        "type": "unlock",
        "name": "diamond ring",
        "price": 500,
        "currency": "quid",
        "unlock_key": "marriage_pass",
        "description": "lets you propose using !marry 💍",
        "inspect_description": (
            "a polished silver band with a clean cut diamond\n\n"
            "required to use !marry\n"
            "purchased from the shop"
        ),
        "emoji": "💍",
    },
    "botadmin": {
        "type": "role",
        "name": "bot admin",
        "price": None,
        "dynamic_price": True,
        "currency": "quid",
        "role_id": AIRole,
        "description": "grants admin permissions + testing channel"
    },
    "vacation_sigwater": {
        "type": "vacation", "name": "sigwater", "price": 1,
        "currency": "quid",
        "role_id": SIGWATER_ROLE, "permanent": True,
        "description": "permanent access to sigwater (repurchase to re-grant role)",
    },
    "vacation_houseofvlads": {
        "type": "vacation", "name": "house of vlads", "price": 2,
        "currency": "quid",
        "role_id": HOUSEOFVLADS_ROLE, "permanent": True,
        "requires_unlock": "bone_emblem",
        "description": "permanent access to house of vlads. requires bone emblem. (!i bone emblem)",
    },
    "vacation_minneapolis": {
        "type": "vacation", "name": "minneapolis", "price": 100,
        "currency": "quid",
        "role_id": MINNEAPOLIS_ROLE, "permanent": True,
        "description": "permanent access to minneapolis",
    },
    "vacation_icypeaks": {
        "type": "vacation", "name": "the icy peaks", "price": 169,
        "currency": "quid",
        "role_id": ICY_PEAKS_ROLE, "permanent": True,
        "description": "permanent access to the icy peaks",
    },
    "vacation_heaven": {
        "type": "vacation", "name": "heaven", "price": 300,
        "currency": "quid",
        "role_id": HEAVEN_ROLE, "permanent": True,
        "description": "permanent access to heaven",
    },
    "vacation_dreamsky": {
        "type": "vacation_info", "name": "the dream sky", "price": 0,
        "currency": "quid",
        "description": "ascend beyond heaven. requires the dreamsky trident. use !ascend in heaven.",
    },
    "vacation_hell": {
        "type": "vacation_info", "name": "hell", "price": 0,
        "currency": "quid",
        "description": "9 layers of hell. requires the outlandish key. use !craft key.",
    },
}

SECRET_SHOP_ITEMS = {
    "xp_boost": {
        "type": "unlock",
        "name": "xp booster 5000",
        "price": 1000,
        "currency": "quid",
        "unlock_key": "xp_boost",
        "description": "permanent 2x xp gain"
    },
    "no_debt": {
        "type": "unlock",
        "name": "debt free pact",
        "price": 1000,
        "currency": "quid",
        "unlock_key": "no_debt",
        "description": "prevents negative balance jail forever"
    },
    "sigs_potion": {
        "type": "consumable",
        "name": "sig's potion",
        "price": 75_000,
        "currency": "quid",
        "unlock_key": "sigs_potion_owned",
        "description": "revives a dead pet instantly. single use.",
        "inspect_description": "a glowing vial of murky water sourced from the depths of sigwater.\n\nuse !use potion to revive your dead pet.\nsingle use. purchased from the secret shop.",
        "emoji": "🧪",
        "consumable": True,
    },
    "golden_receipt": {
        "type": "consumable",
        "name": "golden receipt",
        "price": 120_000,
        "currency": "quid",
        "description": "fight the tax collector. use with !use receipt.",
        "inspect_description": "a gilded slip of paper stamped with a government seal.\n\nuse !use receipt to challenge the tax collector in his office.\nsingle use. purchased from the secret shop.",
        "emoji": "🧾",
        "consumable": True,
    },
}

MINNEAPOLIS_ITEMS = {
    "cologne": {
        "type": "unlock",
        "name": "cologne",
        "price": 1500,
        "currency": "quid",
        "unlock_key": "cologne",
        "description": "makes you smell professional",
        "inspect_description": (
            "a suspiciously strong smelling cologne\n\n"
            "earn extra quid when using !work\n"
            "purchased from !shop in minneapolis"
        ),
        "emoji": "🧴",
    },
}

KEY_SHOP_ITEMS = {
    "golden_gate_key": {
        "type": "unlock",
        "name": "golden gate key",
        "price": 5000,
        "currency": "evil",
        "unlock_key": "golden_gate_key",
        "description": "entry to the parthenon gauntlet.",
        "inspect_description": (
            "a heavy golden key etched with the faces of twelve gods.\n\n"
            "use `!battle` in the parthenon.\n"
            "purchased from treachery"
        ),
        "emoji": "🗝️",
    },
#    "walkie_talkie": {
#        "type": "vacation",
#        "name": "walkie talkie",
#        "price": 2,
#        "currency": "evil",
#        "role_id": 0,
#        "permanent": True,
#        "description": "unlocks #hallway",
#        "inspect_description": (
#            "purchased from treachery"
#        ),
#        "emoji": "📻",
#    },
}

ALL_ITEMS = {**SHOP_ITEMS, **SECRET_SHOP_ITEMS, **MINNEAPOLIS_ITEMS, **KEY_SHOP_ITEMS}

ALL_ITEMS["bone_emblem"] = {
    "type": "unlock",
    "name": "bone emblem",
    "description": "a mysterious emblem obtained through special means. Required to access House of Vlads.",
    "inspect_description": (
        "a bony emblem with strange powers, obtained through working in the icy peaks.\n"
        "it is required to visit the house of vlads."
    ),
    "emoji": "🦴",
    "unlock_key": "bone_emblem"
}

NORMAL_ITEMS = {
    k: v for k, v in SHOP_ITEMS.items()
    if v["type"] not in ("vacation", "vacation_info")
}

VACATION_ITEMS = {
    k: v for k, v in SHOP_ITEMS.items()
    if v["type"] in ("vacation", "vacation_info")
}

suits = ["♠", "♥", "♦", "♣"]
ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def ihaveafriendhisnameisutc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt

def create_deck():
    return [f"{rank}{suit}" for suit in suits for rank in ranks]

def card_value(card):
    rank = card[:-1]
    if rank in ["J", "Q", "K"]:
        return 10
    elif rank == "A":
        return 11
    return int(rank)

def hand_value(hand):
    total = sum(card_value(c) for c in hand)
    aces = sum(1 for c in hand if c.startswith("A"))
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def get_max_page(has_secret: bool):
    return 3 if has_secret else 2

def get_items_for_page(page: int, has_secret: bool, is_minneapolis: bool, is_key_channel: bool = False):
    if page == 0:
        if is_minneapolis:
            items = list(MINNEAPOLIS_ITEMS.items())
        elif is_key_channel:
            items = list(KEY_SHOP_ITEMS.items())
        else:
            items = list(NORMAL_ITEMS.items())
    elif page == 1:
        items = list(VACATION_ITEMS.items())
    elif page == 2:
        items = []
    elif page == 3 and has_secret:
        items = list(SECRET_SHOP_ITEMS.items())
    else:
        items = []

    return items[:ITEMS_PER_PAGE]

def next_lottery_draw_ts():
    now = datetime.datetime.now(datetime.timezone.utc)
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if now >= today_midnight:
        today_midnight += datetime.timedelta(days=1)

    if today_midnight.toordinal() % 2 != 0:
        today_midnight += datetime.timedelta(days=1)

    return int(today_midnight.timestamp())

async def has_all_achievements(bot, user):
    from cogs.achievements.registry import BONUS_ACHIEVEMENT_IDS
    async with db.pool.acquire() as conn:
        bonus_list = list(BONUS_ACHIEVEMENT_IDS)
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM achievements WHERE id != ALL($1::text[])",
            bonus_list
        )
        owned = await conn.fetchval(
            """
            SELECT COUNT(*) FROM user_achievements
            WHERE user_id = $1
            AND achievement_id IN (
                SELECT id FROM achievements WHERE id != ALL($2::text[])
            )
            """,
            user.id, bonus_list
        )
    return owned >= total

async def get_botadmin_price_display() -> int:
    async with db.pool.acquire() as conn:
        val = await conn.fetchval("SELECT MAX(quid) FROM economy")
    return (val or 0) + 1

async def get_botadmin_price(conn) -> int:
    val = await conn.fetchval("SELECT MAX(quid) FROM economy")
    return (val or 0) + 1

async def has_unlock(user_id: int, key: str) -> bool:
    async with db.pool.acquire() as conn:
        value = await conn.fetchval(
            f"SELECT {key} FROM user_unlocks WHERE user_id = $1",
            user_id
        )
    return bool(value)

async def has_no_debt_conn(conn, user_id: int) -> bool:
    return await conn.fetchval(
        "SELECT no_debt FROM user_unlocks WHERE user_id=$1",
        user_id
    ) or False

async def update_negative_state(bot, user_id: int):
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT quid, negative_since FROM economy WHERE user_id = $1",
            user_id
        )
        if not row:
            return

        if await has_no_debt_conn(conn, user_id):
            await conn.execute(
                "UPDATE economy SET negative_since = NULL WHERE user_id = $1",
                user_id
            )
            return

        balance = row["quid"]
        negative_since = row["negative_since"]

        if balance < 0:
            if negative_since is None:
                await conn.execute(
                    "UPDATE economy SET negative_since = NOW() WHERE user_id = $1",
                    user_id
                )
        else:
            await conn.execute(
                "UPDATE economy SET negative_since = NULL WHERE user_id = $1",
                user_id
            )

            for guild in bot.guilds:
                member = guild.get_member(user_id)
                if not member:
                    continue

                jail_role = guild.get_role(JAIL_ROLE_ID)
                if jail_role and jail_role in member.roles:
                    await member.remove_roles(jail_role)

async def send_to_police_jail(bot, member: discord.Member, hours: int):
    guild = member.guild
    police_jail_role = guild.get_role(POLICE_JAIL_ROLE_ID)
    if not police_jail_role:
        return

    await member.add_roles(police_jail_role)
    await hooks.on_jailed(bot, member)

    async def auto_release():
        await asyncio.sleep(hours * 1800)
        try:
            await member.remove_roles(police_jail_role)
        except:
            pass 

    bot.loop.create_task(auto_release())

def requires_crime_pass():
    async def predicate(ctx):
        return await has_unlock(ctx.author.id, "crime_pass")
    return commands.check(predicate)

def build_shop_embed(page: int, subpage: int, has_secret: bool, is_minneapolis: bool, is_key_channel: bool = False, botadmin_price: int = None):
    from cogs.fishing.fishingcommands import SHOP_RODS

    embed = discord.Embed(title="shop", color=discord.Color.blurple())

    def add_items(items: dict):
        for item in items.values():
            currency = item.get("currency", "quid")
            emoji = QUID_EMOJI if currency == "quid" else EVIL_EMOJI
            price = item.get("price")
            if item.get("dynamic_price"):
                price_display = f"{botadmin_price:,}" if botadmin_price is not None else "?"
                name_str = f"{item['name']} – {price_display} {emoji}"
            elif price is not None and not (item.get("type") == "vacation_info"):
                name_str = f"{item['name']} – {price} {emoji}"
            else:
                name_str = item["name"]
            embed.add_field(
                name=name_str,
                value=item.get("description", "No description"),
                inline=False
            )

    if page == 0:
        if is_minneapolis:
            embed.description = "exclusive items from minneapolis"
            add_items(MINNEAPOLIS_ITEMS)
        elif is_key_channel:
            embed.description = "watch"
            add_items(KEY_SHOP_ITEMS)
        else:
            embed.description = "buy permanent perks using your quid"
            add_items(NORMAL_ITEMS)

    elif page == 1:
        embed.description = "buy tickets to see other places"
        add_items(VACATION_ITEMS)

    elif page == 2:
        if subpage == 0:
            embed.description = "buy a rod to start fishing  *(page 1/2)*"
            for rod in SHOP_RODS.values():
                embed.add_field(
                    name=f"{rod['emoji']} {rod['name']} – {rod['price']} {QUID_EMOJI}",
                    value=rod["description"],
                    inline=False,
                )
            from cogs.fishing.fishingcommands import RODS
            pf = RODS["pitchfork"]
            embed.add_field(
                name=f"{pf['emoji']} {pf['name']} - consume dreamsky trident",
                value=pf["description"],
                inline=False,
            )
        else:
            from cogs.fishing.fishingcommands import BAIT_ITEMS
            embed.description = "single use items that boost your next cast  *(page 2/2)*"
            for bait in BAIT_ITEMS.values():
                embed.add_field(
                    name=f"{bait['emoji']} {bait['name']} - {bait['price']} {QUID_EMOJI}",
                    value=bait["description"],
                    inline=False,
                )

    elif page == 3 and has_secret:
        embed.description = "very secret and very shop"
        add_items(SECRET_SHOP_ITEMS)

    return embed

class LeaveSigwaterView(discord.ui.View):
    def __init__(self, bot, user):
        super().__init__()
        self.bot = bot
        self.user = user

    @discord.ui.button(label="yes", style=discord.ButtonStyle.danger)
    async def yes(self, interaction, button):
        if interaction.user.id != self.user.id:
            return

        async with db.pool.acquire() as conn:
            quid = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", self.user.id)
            if quid < 250:
                return await interaction.response.send_message("not enough quid", ephemeral=True)

            await conn.execute("UPDATE economy SET quid = quid - 250 WHERE user_id=$1", self.user.id)

        role = interaction.guild.get_role(SIGWATER_ROLE)
        await self.user.remove_roles(role)

        await interaction.response.edit_message(content="you escaped sigwater.", view=None, embed=None)

    @discord.ui.button(label="no", style=discord.ButtonStyle.secondary)
    async def no(self, interaction, button):
        await interaction.response.edit_message(content="you stay in sigwater.", view=None)

class BailView(discord.ui.View):
    def __init__(self, bot, payer, target, amount):
        super().__init__(timeout=60)
        self.bot = bot
        self.payer = payer
        self.target = target
        self.amount = amount

    @discord.ui.button(
        label="pay bail",
        style=discord.ButtonStyle.danger,
        custom_id="pay_bail"
    )
    async def pay(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.payer.id:
            return await interaction.response.send_message(
                "this isn't your bail",
                ephemeral=True
            )

        async with db.pool.acquire() as conn:
            payer_balance = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1",
                self.payer.id
            ) or 0

            if payer_balance < self.amount:
                return await interaction.response.send_message(
                    "you don't have enough quid",
                    ephemeral=True
                )

            await conn.execute(
                "UPDATE economy SET quid = quid - $1 WHERE user_id = $2",
                self.amount, self.payer.id
            )

            await conn.execute(
                """
                UPDATE economy
                SET quid = 0, negative_since = NULL
                WHERE user_id = $1
                """,
                self.target.id
            )

        await update_negative_state(self.bot, self.payer.id)
        await update_negative_state(self.bot, self.target.id)

        jail_role = interaction.guild.get_role(JAIL_ROLE_ID)
        if jail_role in self.target.roles:
            await self.target.remove_roles(jail_role)

        await interaction.response.edit_message(
            content=f"{self.target.mention} was bailed out by {self.payer.mention}",
            view=None,
            embed=None
        )

class ShopCategorySelect(discord.ui.Select):
    def __init__(self, view: "ShopView"):
        self.view_ref = view

        options = [
            discord.SelectOption(label="items", value="0", emoji="🛒", default=(view.page == 0)),
            discord.SelectOption(label="vacations", value="1", emoji="🎟️", default=(view.page == 1)),
            discord.SelectOption(label="fishing", value="2", emoji="🎣", default=(view.page == 2)),
        ]
        if view.has_secret:
            options.append(discord.SelectOption(label="secret shop", value="3", emoji="🔒", default=(view.page == 3)))

        super().__init__(
            placeholder="browse categories...",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        new_page = int(self.values[0])

        if new_page == 3 and not await has_all_achievements(interaction.client, interaction.user):
            return await interaction.response.send_message(
                "you haven't unlocked this page.",
                ephemeral=True
            )

        self.view_ref.page = new_page
        self.view_ref.subpage = 0
        self.view_ref.build_buttons()
        _ba_price = await get_botadmin_price_display() if new_page == 0 else None
        await interaction.response.edit_message(
            embed=build_shop_embed(
                self.view_ref.page,
                self.view_ref.subpage,
                self.view_ref.has_secret,
                self.view_ref.is_minneapolis,
                self.view_ref.is_key_channel,
                botadmin_price=_ba_price,
            ),
            view=self.view_ref
        )

class FishingPrevButton(discord.ui.Button):
    def __init__(self, view: "ShopView"):
        super().__init__(label="◀", style=discord.ButtonStyle.success, row=2, disabled=(view.subpage == 0))
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        self.view_ref.subpage = 0
        self.view_ref.build_buttons()
        _ba_price = await get_botadmin_price_display() if self.view_ref.page == 0 else None
        await interaction.response.edit_message(
            embed=build_shop_embed(
                self.view_ref.page,
                self.view_ref.subpage,
                self.view_ref.has_secret,
                self.view_ref.is_minneapolis,
                self.view_ref.is_key_channel,
                botadmin_price=_ba_price,
            ),
            view=self.view_ref
        )

class FishingNextButton(discord.ui.Button):
    def __init__(self, view: "ShopView"):
        super().__init__(label="▶", style=discord.ButtonStyle.success, row=2, disabled=(view.subpage == 1))
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        self.view_ref.subpage = 1
        self.view_ref.build_buttons()
        _ba_price = await get_botadmin_price_display() if self.view_ref.page == 0 else None
        await interaction.response.edit_message(
            embed=build_shop_embed(
                self.view_ref.page,
                self.view_ref.subpage,
                self.view_ref.has_secret,
                self.view_ref.is_minneapolis,
                self.view_ref.is_key_channel,
                botadmin_price=_ba_price,
            ),
            view=self.view_ref
        )

class ShopView(discord.ui.View):
    def __init__(self, bot, user, has_secret, is_minneapolis=False, is_key_channel=False, page=0):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.page = page
        self.subpage = 0
        self.has_secret = has_secret
        self.is_minneapolis = is_minneapolis
        self.is_key_channel = is_key_channel
        self.build_buttons()

    async def init_secret(self):
        self.has_secret = await has_all_achievements(self.bot, self.user)
        self.build_buttons()

    def build_buttons(self):
        from cogs.fishing.fishingcommands import SHOP_RODS, RodShopButton

        self.clear_items()

        self.add_item(ShopCategorySelect(self))

        if self.page == 2:
            if self.subpage == 0:
                for rod_id, rod in SHOP_RODS.items():
                    self.add_item(RodShopButton(rod_id, rod))
                self.add_item(PitchforkShopButton())
            else:
                from cogs.fishing.fishingcommands import BAIT_ITEMS, BaitShopButton
                for bait_id, bait in BAIT_ITEMS.items():
                    self.add_item(BaitShopButton(bait_id, bait))     
            self.add_item(FishingPrevButton(self))
            self.add_item(FishingNextButton(self))
        else:
            items = get_items_for_page(self.page, self.has_secret, self.is_minneapolis, self.is_key_channel)
            for item_id, item in items:
                if item.get("type") == "vacation_info":
                    continue
                self.add_item(ShopButton(item_id, item))

class PitchforkShopButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🔱 pitchfork", style=discord.ButtonStyle.danger, custom_id="shop_craft_pitchfork")

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        async with db.pool.acquire() as conn:
            has_t = await conn.fetchval("SELECT 1 FROM user_owned_rods WHERE user_id=$1 AND rod_id='dreamsky_trident'", member.id)
            if not has_t:
                return await interaction.response.send_message("❌ you need the **🔱 dreamsky trident** to forge the pitchfork.", ephemeral=True)
            has_p = await conn.fetchval("SELECT 1 FROM user_owned_rods WHERE user_id=$1 AND rod_id='pitchfork'", member.id)
            if has_p:
                return await interaction.response.send_message("❌ you already own the pitchfork.", ephemeral=True)
            await conn.execute("DELETE FROM user_owned_rods WHERE user_id=$1 AND rod_id='dreamsky_trident'", member.id)
            await conn.execute("INSERT INTO user_owned_rods (user_id,rod_id) VALUES ($1,'pitchfork') ON CONFLICT DO NOTHING", member.id)
        from cogs.fishing.fishingcommands import get_equipped_rod, set_equipped_rod
        if await get_equipped_rod(member.id) == "dreamsky_trident":
            await set_equipped_rod(member.id, "pitchfork")
        await interaction.response.send_message(
            "🔥 **dreamsky trident consumed.** the **🔱 pitchfork** is yours.\ncatches 3 fish.",
            ephemeral=True
        )
        from cogs.achievements import hooks as ach_hooks
        await ach_hooks.on_pitchfork_forged(interaction.client, member)


class ShopButton(discord.ui.Button):
    def __init__(self, item_id, item):
        super().__init__(
            label=f"{item['name']}",
            style=discord.ButtonStyle.primary,
            custom_id=f"shop_buy_{item_id}"
        )
        self.item_id = item_id
        self.item = item

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        guild = interaction.guild
        item = self.item

        async with db.pool.acquire() as conn:
            role = None

            if item["type"] == "role":
                role = guild.get_role(item["role_id"])
                if not role:
                    return await interaction.response.send_message(
                        "❌ role no longer exists",
                        ephemeral=True
                    )

                if role in member.roles:
                    return await interaction.response.send_message(
                        "❌ you already own this item",
                        ephemeral=True
                    )

            elif item["type"] == "unlock":
                owned = await conn.fetchval(
                    f"SELECT {item['unlock_key']} FROM user_unlocks WHERE user_id = $1",
                    member.id
                )
                if owned:
                    return await interaction.response.send_message(
                        "❌ you already own this item",
                        ephemeral=True
                    )

            currency = item.get("currency", "quid")

            if currency == "quid":
                if item.get("dynamic_price"):
                    await conn.execute("SELECT pg_advisory_xact_lock(987654321)")
                    live_price = await get_botadmin_price(conn)

                    balance = await conn.fetchval(
                        "SELECT quid FROM economy WHERE user_id=$1",
                        member.id
                    ) or 0

                    if balance < live_price:
                        return await interaction.response.send_message(
                            f"❌ you can't afford this. current price: **{live_price:,}** {QUID_EMOJI}",
                            ephemeral=True
                        )
                    
                    await conn.execute(
                        "UPDATE economy SET quid = quid - $1 WHERE user_id=$2",
                        live_price, member.id
                    )
                    item = dict(item)
                    item["price"] = live_price

                else:
                    balance = await conn.fetchval(
                        "SELECT quid FROM economy WHERE user_id=$1",
                        member.id
                    ) or 0

                    if balance < item["price"]:
                        return await interaction.response.send_message(
                            "❌ you don't have enough quid",
                            ephemeral=True
                        )

                    await conn.execute(
                        "UPDATE economy SET quid = quid - $1 WHERE user_id=$2",
                        item["price"], member.id
                    )

            elif currency == "evil":
                balance = await conn.fetchval(
                    "SELECT amount FROM evil_quid WHERE user_id=$1",
                    member.id
                ) or 0

                if balance < item["price"]:
                    return await interaction.response.send_message(
                        "❌ you don't have enough evil quid",
                        ephemeral=True
                    )

                await conn.execute(
                    "UPDATE evil_quid SET amount = amount - $1 WHERE user_id=$2",
                    item["price"], member.id
                )

            if item["type"] == "role":
                await member.add_roles(role)

            elif item["type"] == "unlock":
                await conn.execute(
                    f"""
                    INSERT INTO user_unlocks (user_id, {item['unlock_key']})
                    VALUES ($1, TRUE)
                    ON CONFLICT (user_id)
                    DO UPDATE SET {item['unlock_key']} = TRUE
                    """,
                    member.id
                )
            
                await update_negative_state(interaction.client, member.id)

            elif item["type"] == "refund":
                await conn.execute(
                    "UPDATE economy SET quid = quid + $1 WHERE user_id = $2",
                    item["refund"],
                    member.id
                )

            elif item["type"] == "consumable":
                await conn.execute(
                    """
                    INSERT INTO user_inventory (user_id, item_id, quantity)
                    VALUES ($1, $2, 1)
                    ON CONFLICT (user_id, item_id)
                    DO UPDATE SET quantity = user_inventory.quantity + 1
                    """,
                    member.id, self.item_id
                )

            elif item["type"] == "vacation":
                if req := item.get("requires_unlock"):
                    has_req = await conn.fetchval(f"SELECT {req} FROM user_unlocks WHERE user_id=$1", member.id)
                    if not has_req:
                        await conn.execute("UPDATE economy SET quid=quid+$1 WHERE user_id=$2", item["price"], member.id)
                        return await interaction.response.send_message(
                            f"❌ you need the **{req.replace('_',' ')}** to access this location.",
                            ephemeral=True
                        )
                already_owns = await conn.fetchval(
                    "SELECT 1 FROM user_inventory WHERE user_id=$1 AND item_id=$2",
                    member.id, self.item_id
                )
                if already_owns:
                    await conn.execute("UPDATE economy SET quid=quid+$1 WHERE user_id=$2", item["price"], member.id)
                    charge_note = " (re-granted, no charge)"
                else:
                    await conn.execute("INSERT INTO user_inventory (user_id,item_id) VALUES ($1,$2) ON CONFLICT DO NOTHING", member.id, self.item_id)
                    charge_note = f" (-{item['price']} {QUID_EMOJI})" if item["price"] > 0 else ""
                if role_id := item.get("role_id"):
                    role = guild.get_role(role_id)
                    if role and role not in member.roles:
                        await member.add_roles(role)
                place = self.item_id.replace("vacation_", "")
                await hooks.on_visit_vacation(interaction.client, member, place)
                return await interaction.response.send_message(
                    f"✅ **{item['name']}** access granted{charge_note}", ephemeral=True
                )

            elif item["type"] == "vacation_info":
                await conn.execute("UPDATE economy SET quid=quid+$1 WHERE user_id=$2", item.get("price",0), member.id)
                return await interaction.response.send_message(
                    f"ℹ️ **{item['name']}**: {item['description']}", ephemeral=True
                )

        if item.get("unlock_key") == "marriage_pass":
            await hooks.on_buy_ring(interaction.client, member)
        elif item.get("unlock_key") == "cologne":
            await hooks.on_buy_cologne(interaction.client, member)

        currency = item.get("currency", "quid")
        emoji = QUID_EMOJI if currency == "quid" else EVIL_EMOJI

        await interaction.response.send_message(
            f"✅ purchased **{item['name']}** for {item['price']} {emoji}",
            ephemeral=True
        )

class PrevPageButton(discord.ui.Button):
    def __init__(self, view: ShopView):
        super().__init__(
            label="◀",
            style=discord.ButtonStyle.success,
            row=1,
            disabled=view.page == 0
        )
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        self.view_ref.page -= 1
        self.view_ref.build_buttons()
        _ba_price = await get_botadmin_price_display() if self.view_ref.page == 0 else None
        await interaction.response.edit_message(
            embed=build_shop_embed(self.view_ref.page, self.view_ref.subpage, self.view_ref.has_secret, self.view_ref.is_minneapolis, self.view_ref.is_key_channel, botadmin_price=_ba_price),
            view=self.view_ref
        )

class NextPageButton(discord.ui.Button):
    def __init__(self, view: ShopView):
        super().__init__(
            label="▶",
            style=discord.ButtonStyle.success,
            row=1,
            disabled=view.page >= view.max_page
        )
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        self.view_ref.page += 1

        if self.view_ref.page == 3:
            if not await has_all_achievements(interaction.client, interaction.user):
                self.view_ref.page -= 1
                return await interaction.response.send_message(
                    "you haven't unlocked this page.",
                    ephemeral=True
                )

        self.view_ref.build_buttons()
        _ba_price = await get_botadmin_price_display() if self.view_ref.page == 0 else None
        await interaction.response.edit_message(
            embed=build_shop_embed(self.view_ref.page, self.view_ref.subpage, self.view_ref.has_secret, self.view_ref.is_minneapolis, self.view_ref.is_key_channel, botadmin_price=_ba_price),
            view=self.view_ref
        )

class QuidTopView(discord.ui.View):
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
        LIMIT_POOL = 50

        async with db.pool.acquire() as conn:
            econ_rows = await conn.fetch(
                f"""
                SELECT user_id, quid
                FROM economy
                ORDER BY quid DESC
                LIMIT {LIMIT_POOL}
                """
            )

            scores = []

            for er in econ_rows:
                uid = er["user_id"]

                bank = await conn.fetchrow(
                    "SELECT loan_amount, cd_amount FROM finance_bank WHERE user_id=$1", uid
                )

                stocks = await conn.fetch(
                    "SELECT ticker, shares FROM finance_portfolio WHERE user_id=$1", uid
                )

                funds = await conn.fetch(
                    "SELECT amount FROM finance_index_investments WHERE user_id=$1", uid
                )

                stock_val = 0
                for r in stocks:
                    price = await get_stock_price(r["ticker"])
                    stock_val += price * r["shares"]

                fund_val = sum(r["amount"] for r in funds)

                loan    = bank["loan_amount"] if bank else 0
                cd      = bank["cd_amount"] if bank else 0

                net = (er["quid"] or 0) + stock_val + fund_val + cd - loan
                scores.append((uid, net))

        scores.sort(key=lambda x: x[1], reverse=True)

        start = (self.page - 1) * self.page_size
        page_rows = scores[start:start + self.page_size]

        embed = discord.Embed(
            title="🏆 net worth leaderboard",
            description="who's actually rich (real assets)",
            color=discord.Color.gold()
        )

        embed.set_thumbnail(url=self.ctx.guild.icon)

        if not page_rows:
            embed.add_field(
                name="empty",
                value="no data on this page",
                inline=False
            )

        medals = ["🥇", "🥈", "🥉"]

        for idx, (uid, net) in enumerate(page_rows, start=1):
            position = idx + (self.page_size * (self.page - 1))

            user = self.ctx.guild.get_member(uid)
            if not user:
                try:
                    user = await self.bot.fetch_user(uid)
                except:
                    user = None

            name = user.display_name if user else f"Unknown ({uid})"
            prefix = medals[position - 1] if position <= 3 else f"#{position}"

            embed.add_field(
                name=f"{prefix} – {name}",
                value=f"{QUID_EMOJI} **{net:,}**",
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

class EconomyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not self.jail_check_task.is_running():
            self.jail_check_task.start()

        if not self.sigwater_tax.is_running():
            self.sigwater_tax.start()

        if not self.income_reminder_task.is_running():
            self.income_reminder_task.start()

    @commands.command(name="balance", aliases=["cash", "bal", "money", "quid", "bank", "nw", "networth"], help="see your money", usage="!balance")
    async def balance(self, ctx, member: typing.Optional[discord.Member] = None):
        from cogs.finance.financecommands import (
            ensure_bank, get_bank_row, get_stock_price,
            INTEREST_RATE_LOAN, INDEX_FUNDS,
        )
        from cogs.hell.hellcommands import EVIL_EMOJI
 
        user = member or ctx.author
 
        async with db.pool.acquire() as conn:
            quid = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id=$1", user.id
            ) or 0

            await ensure_bank(conn, user.id)
            bank = await get_bank_row(conn, user.id)
 
            evil_row = await conn.fetchrow(
                "SELECT amount FROM evil_quid WHERE user_id=$1", user.id
            )
            evil = evil_row["amount"] if evil_row is not None else None
 
            job_row = await conn.fetchrow(
                "SELECT job_id, last_collected FROM user_jobs WHERE user_id=$1", user.id
            )
 
            fund_rows = await conn.fetch(
                "SELECT fund, amount FROM finance_index_investments WHERE user_id=$1", user.id
            )
 
            stock_rows = await conn.fetch(
                "SELECT ticker, shares FROM finance_portfolio WHERE user_id=$1", user.id
            )
 
            margin = await conn.fetchval(
                "SELECT margin_used FROM finance_margin WHERE user_id=$1", user.id
            ) or 0
 
        stock_val = 0
        for row in stock_rows:
            p = await get_stock_price(row["ticker"])
            stock_val += p * row["shares"]
 
        loan     = bank["loan_amount"] if bank else 0
        cd       = bank["cd_amount"]   if bank else 0
        fund_val = sum(r["amount"] for r in fund_rows)
        net      = quid + stock_val + fund_val + cd - loan - margin
 
        embed = discord.Embed(
            title=f"{user.display_name}'s balance",
            color=discord.Color.green()
        )
 
        embed.add_field(name=f"{QUID_EMOJI} wallet", value=f"**{quid:,}**",    inline=True)
 
        if loan > 0:
            embed.add_field(
                name="💳 loan",
                value=f"**{loan:,}** {QUID_EMOJI} ({INTEREST_RATE_LOAN*100:.0f}%/day)",
                inline=False
            )
 
        if bank and bank["cd_amount"] > 0 and bank["cd_matures_at"]:
            ts = int(bank["cd_matures_at"].timestamp())
            embed.add_field(
                name="📀 cd",
                value=f"**{cd:,}** {QUID_EMOJI} · matures <t:{ts}:R>",
                inline=False
            )
 
        if stock_val > 0:
            embed.add_field(name="📈 stocks", value=f"**{stock_val:,}** {QUID_EMOJI}", inline=True)
 
        if margin > 0:
            embed.add_field(name="⚡ margin debt", value=f"**-{margin:,}** {QUID_EMOJI}", inline=True)
 
        for fr in fund_rows:
            fund = INDEX_FUNDS.get(fr["fund"], {})
            embed.add_field(
                name=f"{fund.get('emoji', '📊')} {fund.get('name', fr['fund'])}",
                value=f"**{fr['amount']:,}** {QUID_EMOJI}",
                inline=True
            )

        if evil is not None:
            embed.add_field(
                name=f"{EVIL_EMOJI} evil quid",
                value=f"**{evil:,}**",
                inline=True
            )
 
        if job_row:
            job_def = JOBS.get(job_row["job_id"])
            if job_def:
                now  = datetime.datetime.now(datetime.timezone.utc)
                last = job_row["last_collected"]
                if last and last.tzinfo is None:
                    last = last.replace(tzinfo=datetime.timezone.utc)
                ready  = last is None or (now - last).total_seconds() >= job_def["interval_hours"] * 3600
                status = f"**{job_def['name']}** · {'✅ ready to collect' if ready else 'income pending'}"
                embed.add_field(name="💼 job", value=status, inline=False)
 
        embed.set_footer(text=f"net worth: {net:,} {QUID_EMOJI}")
 
        if user == ctx.author:
            for threshold, ach in [
                (1_000,  "finance.networth.1k"),
                (5_000,  "finance.networth.5k"),
                (10_000, "finance.networth.10k"),
                (50_000, "finance.networth.50k"),
            ]:
                if net >= threshold:
                    from cogs.finance.financecommands import _fire as finance_fire
                    await finance_fire(self.bot, ctx.author, ach)
 
        await ctx.send(embed=embed)

    @commands.command(hidden=True, usage="!leave")
    async def leave(self, ctx):
        SIGWATER_ROLE = ctx.guild.get_role(1466604056230498355)
        if SIGWATER_ROLE not in ctx.author.roles:
            return await ctx.send("you are not in sigwater")

        embed = discord.Embed(
            title="leave sigwater?",
            description="you must pay **250 quid** to leave sigwater.",
            color=discord.Color.red()
        )

        await ctx.send(embed=embed, view=LeaveSigwaterView(self.bot, ctx.author))

    @commands.command(name="shop", help="purchase items and more", usage="!shop")
    async def shop(self, ctx):
        has_secret = await has_all_achievements(self.bot, ctx.author)

        is_minneapolis = ctx.channel.id == MINNEAPOLIS_CHANNEL
        is_key_channel = ctx.channel.id == KEY_CHANNEL

        if is_key_channel:
            is_minneapolis = False

        view = ShopView(self.bot, ctx.author, has_secret, is_minneapolis, is_key_channel)
        _ba_price = await get_botadmin_price_display()
        embed = build_shop_embed(0, 0, has_secret, is_minneapolis, is_key_channel, botadmin_price=_ba_price)

        await ctx.send(embed=embed, view=view)

    @commands.command(name="i", help="inspect an item", usage="!i <item name>")
    async def inspect_item(self, ctx, *, item_name: str):

        item_name = item_name.lower()

        found_item = None

        for key, item in ALL_ITEMS.items():
            if (
                key.lower() == item_name
                or item["name"].lower() == item_name
            ):
                found_item = item
                break

        if not found_item:
            return await ctx.send("that item doesn't exist.")

        emoji = found_item.get("emoji", "📦")
        inspect_text = found_item.get(
            "inspect_description"
        )

        embed = discord.Embed(
            title=f"{emoji} {found_item['name']}",
            description=inspect_text,
            color=discord.Color(0xDC143C)
        )

        await ctx.send(embed=embed)

    @commands.command(
        name="quidtop",
        aliases=["topnw", "richlist"],
        help="top net worths in the server",
        usage="!quidtop"
    )
    async def richlist(self, ctx: commands.Context):
        page_size = 5

        async with db.pool.acquire() as conn:
            total_users = await conn.fetchval(
                "SELECT COUNT(*) FROM economy"
            )

        if total_users == 0:
            return await ctx.send("no economy data exists yet")

        total_pages = (total_users + page_size - 1) // page_size

        view = QuidTopView(
            bot=self.bot,
            ctx=ctx,
            total_pages=total_pages,
            page_size=page_size
        )

        embed = await view.generate_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(name="convert", help="turn your xp into fresh quid", usage="!convert")
    async def convert(self, ctx):
        async with db.pool.acquire() as conn:
            xp = await conn.fetchval(
                "SELECT xp FROM xp WHERE user_id = $1",
                ctx.author.id
            )

            if not xp:
                return await ctx.send("you don't have ANY XP to convert")

            econ = await conn.fetchrow(
                "SELECT xp_converted FROM economy WHERE user_id = $1",
                ctx.author.id
            )
            xp_converted = econ["xp_converted"] if econ else 0

            new_xp = xp - xp_converted
            if new_xp < XP_PER_QUID:
                return await ctx.send("not enough new XP to convert")

            quid = new_xp // XP_PER_QUID

            await conn.execute(
                """
                INSERT INTO economy (user_id, quid, xp_converted)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    quid = economy.quid + $2,
                    xp_converted = $3
                """,
                ctx.author.id,
                quid,
                xp_converted + quid * XP_PER_QUID
            )

        await ctx.send(
            f"{ctx.author.display_name} converted XP into {quid:,} {QUID_EMOJI}"
        )

    @commands.command(name="work", help="work your ass off for legal money", usage="!work")
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def work(self, ctx):
        if ctx.channel.id == MINNEAPOLIS_CHANNEL and MINNEAPOLIS_ROLE in [r.id for r in ctx.author.roles]:
            earnings = random.randint(80, 100)
        else:
            earnings = random.randint(30, 59)

        async with db.pool.acquire() as conn:

            has_cologne = await conn.fetchval(
                "SELECT cologne FROM user_unlocks WHERE user_id=$1",
                ctx.author.id
            )

            if has_cologne:
                earnings = int(earnings * 2)
        
            await conn.execute(
                """
                INSERT INTO economy (user_id, quid)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET quid = economy.quid + $2
                """,
                ctx.author.id,
                earnings
            )

        await update_negative_state(self.bot, ctx.author.id)

        if ctx.channel.id == ICY_PEAKS_CHANNEL:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_unlocks (user_id, bone_emblem)
                    VALUES ($1, TRUE)
                    ON CONFLICT (user_id)
                    DO UPDATE SET bone_emblem = TRUE
                    """,
                    ctx.author.id
                )
            emblem_msg = " 🎉 you also obtained the **bone emblem**!"
        else:
            emblem_msg = ""

        await ctx.send(f"{ctx.author.display_name} earned {earnings} {QUID_EMOJI}{emblem_msg}")

        if ctx.channel.id == MINNEAPOLIS_CHANNEL:
            has_role = any(r.id == MINNEAPOLIS_ROLE for r in ctx.author.roles)

            if has_role and random.random() < 0.20:
                async with db.pool.acquire() as conn:
                    already = await conn.fetchval(
                        "SELECT workers_tear FROM user_unlocks WHERE user_id=$1",
                        ctx.author.id
                    )

                    if not already:
                        await conn.execute(
                            """
                            INSERT INTO user_unlocks (user_id, workers_tear)
                            VALUES ($1, TRUE)
                            ON CONFLICT (user_id) DO UPDATE SET workers_tear = TRUE
                            """,
                            ctx.author.id
                        )

                        await ctx.send(
                            f"😢 a **worker's tear** falls from {ctx.author.display_name}'s eye. "
                            f"key component obtained. (`!craft key`)"
                        )
                        from cogs.achievements import hooks
                        await hooks.on_workers_tear(self.bot, ctx.author)

        from cogs.fishing.fishingcommands import HELL_CHANNEL_IDS
        if ctx.channel.id in HELL_CHANNEL_IDS:
            evil = max(1, earnings // 10)
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO evil_quid (user_id,amount) VALUES ($1,$2) ON CONFLICT (user_id) DO UPDATE SET amount=evil_quid.amount+$2",
                    ctx.author.id, evil
                )
            await ctx.send(f"🔥 +{evil} evil quid")

        from cogs.achievements import hooks
        await hooks.on_work(self.bot, ctx.author)
        await hooks.on_work_big(self.bot, ctx.author, earnings)

    @commands.command(name="crime", help="work your ass off for illegal money", usage="!crime")
    async def crime(self, ctx):
        if not await has_unlock(ctx.author.id, "crime_pass"):
            return await ctx.send("❌ you need the **CRIME PASS** to use this command (!i crime for more info)")

        now = discord.utils.utcnow().timestamp()
        last = getattr(self, "_crime_cooldowns", {}).get(ctx.author.id, 0)
        if now - last < 3600:
            remaining = int(3600 - (now - last))
            retry_at = int(now + remaining)
            return await ctx.send(f"you're still laying low. try again <t:{retry_at}:R>")

        if not hasattr(self, "_crime_cooldowns"):
            self._crime_cooldowns = {}
        self._crime_cooldowns[ctx.author.id] = now

        if ctx.channel.id == MINNEAPOLIS_CHANNEL and MINNEAPOLIS_ROLE in [r.id for r in ctx.author.roles]:
            await ctx.author.send("you have been sent to jail for 30 minutes, due to committing a crime in minneapolis.")
            await send_to_police_jail(self.bot, ctx.author, 1)

            return

        amount = random.randint(100, 350)
        win = random.choice([True, False])

        async with db.pool.acquire() as conn:
            if win:
                await conn.execute(
                    "UPDATE economy SET quid = quid + $1 WHERE user_id = $2",
                    amount,
                    ctx.author.id
                )
            else:
                await conn.execute(
                    "UPDATE economy SET quid = quid - $1 WHERE user_id = $2",
                    amount,
                    ctx.author.id
                )
                await hooks.on_crime_failed(
                    self.bot,
                    ctx.author
                )

        await update_negative_state(self.bot, ctx.author.id)

        if win:
            await ctx.send(
                f"💰 **crime successful!!**\n"
                f"you gained **{amount} {QUID_EMOJI}**!!!!!!!!!"
            )
        else:
            await ctx.send(
                f"🚔 **crime failed!!**\n"
                f"you lost **{amount} {QUID_EMOJI}**!!!!!!!!"
            )

        if win:
            from cogs.fishing.fishingcommands import HELL_CHANNEL_IDS
            if ctx.channel.id in HELL_CHANNEL_IDS:
                evil = max(1, amount // 8)
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO evil_quid (user_id,amount) VALUES ($1,$2) ON CONFLICT (user_id) DO UPDATE SET amount=evil_quid.amount+$2",
                        ctx.author.id, evil
                    )
                await ctx.send(f"🔥 +{evil} evil quid")

    @commands.command(name="daily", help="claim your daily quid", usage="!daily")
    async def daily(self, ctx):
        now = datetime.datetime.now(datetime.timezone.utc)
        today = now.date()

        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT last_daily, streak, last_claim_date FROM economy WHERE user_id = $1",
                ctx.author.id
            )

            streak = 0

            if row:
                last_daily = row["last_daily"]
                last_claim_date = row["last_claim_date"]
                streak = row["streak"] or 0

                if last_daily and last_daily.tzinfo is None:
                    last_daily = last_daily.replace(tzinfo=datetime.timezone.utc)

                if last_claim_date == today:
                    return await ctx.send("you already claimed your daily today.")

                if last_claim_date == today - datetime.timedelta(days=1):
                    streak += 1
                else:
                    streak = 1
            else:
                streak = 1

            reward = random.randint(80, 150)

            bonus = MILESTONES.get(streak, 0)
            total = reward + bonus

            await conn.execute(
                """
                INSERT INTO economy (user_id, quid, last_daily, streak, last_claim_date)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    quid = economy.quid + $2,
                    last_daily = $3,
                    streak = $4,
                    last_claim_date = $5
                """,
                ctx.author.id,
                total,
                now,
                streak,
                today
            )

        await update_negative_state(self.bot, ctx.author.id)

        msg = (
            f"you claimed your daily and received **{reward} {QUID_EMOJI}**\n"
        )

        if bonus:
            msg += f"🔥 streak bonus: **+{bonus}**\n"

        msg += f"\nstreak: **{streak} days 🔥**"

        await ctx.send(msg)

        await hooks.on_claim_daily(self.bot, ctx.author)

    @commands.command(name="weekly", help="claim weekly reward", usage="!weekly")
    async def weekly(self, ctx):
        now = datetime.datetime.now(datetime.timezone.utc)

        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT last_weekly FROM economy WHERE user_id = $1",
                ctx.author.id
            )

            last = None
            if row and row["last_weekly"]:
                last = row["last_weekly"]

                if last.tzinfo is None:
                    last = last.replace(tzinfo=datetime.timezone.utc)

                diff = now - last
                if diff.total_seconds() < 7 * 86400:
                    remaining = int(7 * 86400 - diff.total_seconds())
                    return await ctx.send(
                        f"you already claimed weekly. come back <t:{int(now.timestamp()+remaining)}:R>"
                    )

            reward = random.randint(600, 1200)

            await conn.execute(
                """
                INSERT INTO economy (user_id, quid, last_weekly)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    quid = economy.quid + EXCLUDED.quid,
                    last_weekly = EXCLUDED.last_weekly
                """,
                ctx.author.id,
                reward,
                now
            )

        await ctx.send(
            f"weekly reward claimed: **{reward} {QUID_EMOJI}** 💰"
        )
        await hooks.on_claim_weekly(self.bot, ctx.author)

    @commands.command(name="bail", help="bail someone who has been jailed out", usage="!bail (person)")
    async def bail(self, ctx, member: discord.Member):
        async with db.pool.acquire() as conn:
            debt = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1",
                member.id
            )

        if debt is None or debt >= 0:
            return await ctx.send("this person is not in debt")

        embed = discord.Embed(
            title="bail",
            description=(
                f"**target:** {member.mention}\n"
                f"**debt:** {abs(debt)} {QUID_EMOJI}"
            ),
            color=discord.Color.red()
        )

        await ctx.send(
            embed=embed,
            view=BailView(self.bot, ctx.author, member, abs(debt))
        )

    @commands.command(name="escape", help="attempt to escape jail via boss rush", usage="!escape")
    async def escape(self, ctx):
        if ctx.channel.id != JAIL_CHANNEL:
            return await ctx.send("you can only use this command in the jail channel.")

        from cogs.fun.funcommands import (
            run_vladurk_escape, run_sigshark_escape,
            run_dealer_escape, run_socrates_escape
        )

        await ctx.send(embed=discord.Embed(
            title="⛓️ BOSS RUSH - ESCAPE FROM JAIL",
            description=(
                "to escape you must defeat all 4 bosses in order:\n\n"
                "**1.** vladurk\n"
                "**2.** supreme sigshark\n"
                "**3.** the dealer\n"
                "**4.** socrates\n\n"
                "*fail any fight and you stay in jail.*"
            ),
            color=discord.Color.dark_red()
        ))
        await asyncio.sleep(2)

        bosses = [
            ("VLADURK", run_vladurk_escape),
            ("SUPREME SIGSHARK", run_sigshark_escape),
            ("THE DEALER", run_dealer_escape),
            ("SOCRATES", run_socrates_escape),
        ]

        for idx, (name, fight_fn) in enumerate(bosses, 1):
            await ctx.send(embed=discord.Embed(
                title=f"⚔️ BOSS {idx}/4 - {name}",
                description="the fight begins...",
                color=discord.Color.dark_red()
            ))
            await asyncio.sleep(1)

            result = await fight_fn(self.bot, ctx.channel, ctx.author)

            if not result:
                await ctx.send(embed=discord.Embed(
                    title="⛓️ ESCAPE FAILED",
                    description=(
                        f"**{ctx.author.mention}** was defeated by **{name}**.\n\n"
                        "*the jail cell door slams shut.*"
                    ),
                    color=discord.Color.dark_red()
                ))
                return

            await ctx.send(embed=discord.Embed(
                description=f"✅ **{name}** defeated. keep going.",
                color=discord.Color.green()
            ))
            await asyncio.sleep(1.5)

        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE economy SET quid = 0, negative_since = NULL WHERE user_id = $1",
                ctx.author.id
            )

        await ctx.author.remove_roles(JAIL_ROLE_ID)
        await ctx.author.remove_roles(POLICE_JAIL_ROLE_ID)

        await ctx.send(embed=discord.Embed(
            title="⛓️ ESCAPED",
            description=(
                f"**{ctx.author.mention}** defeated all 4 bosses and walked free.\n\n"
                "*debt cleared. jail role removed.*"
            ),
            color=discord.Color.gold()
        ))

    @commands.command(name="use", help="use a consumable item from your inventory", usage="!use <item>")
    async def use_item(self, ctx, *, item_name: str):
        item_name = item_name.lower().strip()

        ALIASES = {
            "potion": "sigs_potion",
            "sig potion": "sigs_potion",
            "sigs potion": "sigs_potion",
            "receipt": "golden_receipt",
            "golden receipt": "golden_receipt",
        }
        item_id = ALIASES.get(item_name, item_name.replace(" ", "_"))

        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT quantity FROM user_inventory WHERE user_id=$1 AND item_id=$2",
                ctx.author.id, item_id
            )

        if not row or row["quantity"] < 1:
            return await ctx.send(f"❌ you don't have a **{item_id.replace('_', ' ')}** in your inventory.")

        if item_id == "sigs_potion":
            async with db.pool.acquire() as conn:
                pet = await conn.fetchrow(
                    "SELECT id, name, is_dead FROM pets WHERE owner_id=$1 ORDER BY adopted_at DESC LIMIT 1",
                    ctx.author.id
                )

            if not pet:
                return await ctx.send("❌ you don't have a pet to revive.")

            if not pet["is_dead"]:
                return await ctx.send(f"❌ **{pet['name']}** is alive and well. save the potion.")

            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE pets SET is_dead=FALSE, hunger=80, happiness=80 WHERE id=$1",
                    pet["id"]
                )
                await conn.execute(
                    "UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id=$1 AND item_id='sigs_potion'",
                    ctx.author.id
                )

            return await ctx.send(
                f"🧪 the potion glows and spills into **{pet['name']}**'s mouth.\n"
                f"💚 **{pet['name']}** is alive again."
            )

        if item_id == "golden_receipt":
            import datetime as _dt

            channel = self.bot.get_channel(TAX_COLLECTOR_CHANNEL)
            if not channel:
                return await ctx.send("❌ the tax collector's office hasn't been set up yet.")

            async with db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT last_fight FROM enemy_cooldowns WHERE user_id=$1 AND enemy='tax_collector'",
                    ctx.author.id
                )

            if row:
                ce = row["last_fight"] + _dt.timedelta(hours=72)
                if ce > _dt.datetime.now(_dt.timezone.utc):
                    return await ctx.send(
                        f"🧾 the tax collector isn't taking appointments. try again <t:{int(ce.timestamp())}:R>"
                    )

            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE user_inventory SET quantity = quantity - 1 WHERE user_id=$1 AND item_id='golden_receipt'",
                    ctx.author.id
                )

            tc_role = ctx.guild.get_role(TAX_COLLECTOR_ROLE) if TAX_COLLECTOR_ROLE else None
            if tc_role and tc_role not in ctx.author.roles:
                try:
                    await ctx.author.add_roles(tc_role, reason="golden receipt used")
                except discord.Forbidden:
                    pass

            if channel.id != ctx.channel.id:
                await ctx.send(f"🧾 the receipt crumbles in your hand. head to {channel.mention}.")

            from cogs.fun.funcommands import run_tax_collector_fight
            result = await run_tax_collector_fight(self.bot, channel, ctx.author)

            if tc_role and tc_role in ctx.author.roles:
                try:
                    await ctx.author.remove_roles(tc_role, reason="tax collector fight ended")
                except discord.Forbidden:
                    pass

            if result:
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO enemy_cooldowns (user_id, enemy, last_fight)
                        VALUES ($1, 'tax_collector', $2)
                        ON CONFLICT (user_id, enemy) DO UPDATE SET last_fight=EXCLUDED.last_fight
                        """,
                        ctx.author.id, _dt.datetime.now(_dt.timezone.utc)
                    )

                from cogs.achievements import hooks as ach_hooks
                await ach_hooks.on_tax_collector_defeat(self.bot, ctx.author)
            return

        await ctx.send(f"❌ **{item_id.replace('_', ' ')}** has no use effect defined yet.")

    @commands.command(name="addquid", help="add illegal counterfeit money", usage="!addquid (person)")
    @commands.has_role(AIRole)
    async def addquid(self, ctx, member: discord.Member, amount: int):
        async with db.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO economy (user_id, quid) VALUES ($1, $2) "
                "ON CONFLICT (user_id) DO UPDATE SET quid = economy.quid + $2",
                member.id, amount
            )
        
        await update_negative_state(self.bot, member.id)
        await ctx.send(
            f"added {amount:,} {QUID_EMOJI} to {member.mention}'s balance"
        )

    @commands.command(name="jobs", help="browse and buy job positions", usage="!jobs")
    async def jobs(self, ctx):
        async with db.pool.acquire() as conn:
            job_row = await conn.fetchrow(
                "SELECT job_id FROM user_jobs WHERE user_id=$1", ctx.author.id
            )
        current_id = job_row["job_id"] if job_row else None

        embed = discord.Embed(
            title="💼 job board",
            description=(
                "jobs pay passive income collected with `!income`.\n"
                "buy a job with `!hireme <job>`. quit with `!quit`.\n"
            ),
            color=discord.Color.blurple()
        )
        for jid, job in JOBS.items():
            tag = " *(current)*" if jid == current_id else ""
            embed.add_field(
                name=f"{job['emoji']} **{job['name']}**{tag} - {job['price']:,} {QUID_EMOJI}",
                value=(
                    f"{job['description']}\n"
                    f"**{job['income']:,} {QUID_EMOJI}** every **{job['interval_hours']}h**"
                ),
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="hireme", help="buy a job position", usage="!hireme <job>")
    async def hireme(self, ctx, *, job_name: str):
        job_name = job_name.lower().strip()
        match = next(
            (jid for jid, j in JOBS.items()
             if jid == job_name or j["name"].lower() == job_name),
            None
        )
        if not match:
            return await ctx.send(
                f"unknown job. check `!jobs` for the list."
            )
        job = JOBS[match]

        async with db.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT job_id FROM user_jobs WHERE user_id=$1", ctx.author.id
            )
            if existing:
                current = JOBS.get(existing["job_id"], {})
                return await ctx.send(
                    f"you already work as a **{current.get('name', existing['job_id'])}**. "
                    f"use `!quit` first."
                )

            wallet = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id=$1", ctx.author.id
            ) or 0
            if wallet < job["price"]:
                return await ctx.send(
                    f"you need **{job['price']:,}** {QUID_EMOJI} to take this position. "
                    f"you have **{wallet:,}**."
                )

            await conn.execute(
                "UPDATE economy SET quid = quid - $1 WHERE user_id=$2",
                job["price"], ctx.author.id
            )
            await conn.execute(
                """
                INSERT INTO user_jobs (user_id, job_id, hired_at, last_collected)
                VALUES ($1, $2, NOW(), NULL)
                ON CONFLICT (user_id) DO UPDATE
                    SET job_id=EXCLUDED.job_id,
                        hired_at=EXCLUDED.hired_at,
                        last_collected=NULL
                """,
                ctx.author.id, match
            )

        if job_name in (["banker", "vlad banker"]):
            await hooks.on_banker(self.bot, ctx.author)

        await ctx.send(
            f"{job['emoji']} you're now a **{job['name']}**. "
            f"collect **{job['income']:,}** {QUID_EMOJI} every **{job['interval_hours']}h** with `!income`."
        )

    @commands.command(name="income", help="collect your job's passive income", usage="!income")
    async def income(self, ctx):
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT job_id, last_collected FROM user_jobs WHERE user_id=$1",
                ctx.author.id
            )
            if not row:
                return await ctx.send(
                    "you don't have a job. browse positions with `!jobs` and hire yourself with `!hireme`."
                )

            job = JOBS.get(row["job_id"])
            if not job:
                return await ctx.send("your job no longer exists. use `!quit` to clear it.")

            now  = datetime.datetime.now(datetime.timezone.utc)
            last = row["last_collected"]
            if last and last.tzinfo is None:
                last = last.replace(tzinfo=datetime.timezone.utc)

            interval_secs = job["interval_hours"] * 3600
            if last is not None and (now - last).total_seconds() < interval_secs:
                ready_at = int((last + datetime.timedelta(seconds=interval_secs)).timestamp())
                return await ctx.send(
                    f"{job['emoji']} your income isn't ready yet. collect again <t:{ready_at}:R>."
                )

            amount = job["income"]
            await conn.execute(
                "UPDATE economy SET quid = quid + $1 WHERE user_id=$2",
                amount, ctx.author.id
            )
            await conn.execute(
                "UPDATE user_jobs SET last_collected=$1 WHERE user_id=$2",
                now, ctx.author.id
            )

        await update_negative_state(self.bot, ctx.author.id)
        await ctx.send(
            f"{job['emoji']} {job['flavor']}\n"
            f"**+{amount:,}** {QUID_EMOJI} collected."
        )

    @commands.command(name="quit", help="resign from your current job", usage="!quit")
    async def quitjob(self, ctx):
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT job_id FROM user_jobs WHERE user_id=$1", ctx.author.id
            )
            if not row:
                return await ctx.send("you don't have a job to quit.")

            job = JOBS.get(row["job_id"], {})
            await conn.execute("DELETE FROM user_jobs WHERE user_id=$1", ctx.author.id)

        await ctx.send(
            f"you resigned from **{job.get('name', row['job_id'])}**. "
            f"use `!hireme` to find new work."
        )

    @tasks.loop(hours=1)
    async def income_reminder_task(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=10)
    async def jail_check_task(self):
        await self.bot.wait_until_ready()
        now = datetime.datetime.now(datetime.timezone.utc)

        async with db.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT e.user_id, e.negative_since
                FROM economy e
                LEFT JOIN user_unlocks u ON e.user_id = u.user_id
                WHERE e.quid < 0
                AND e.negative_since IS NOT NULL
                AND (u.no_debt IS NULL OR u.no_debt = FALSE)
            """)

        for guild in self.bot.guilds:
            jail_role = guild.get_role(JAIL_ROLE_ID)
            if not jail_role:
                continue

            for row in rows:
                user_id = row["user_id"]
                negative_since = row["negative_since"]

                member = guild.get_member(user_id)
                if not member:
                    continue

                if negative_since.tzinfo is None:
                    negative_since = negative_since.replace(tzinfo=datetime.timezone.utc)

                elapsed_days = (now - negative_since).total_seconds() / 86400

                if elapsed_days >= JAIL_DAYS and jail_role not in member.roles:
                    await member.add_roles(jail_role)

    @tasks.loop(hours=1)
    async def sigwater_tax(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            channel = guild.get_channel(SIGWATER_CHANNEL)
            if not channel:
                continue

            for member in guild.members:
                if SIGWATER_ROLE in [r.id for r in member.roles]:
                    stolen = 50

                    async with db.pool.acquire() as conn:
                        await conn.execute(
                            "UPDATE economy SET quid = quid - $1 WHERE user_id = $2",
                            stolen, member.id
                        )

                    await channel.send(
                        f"💀 the robbers of sigwater have stolen {stolen} {QUID_EMOJI} from {member.mention} for existing."
                    )

JOBS: dict[str, dict] = {
    "fisherman": {
        "name": "milkman",
        "emoji": "🥛",
        "description": "go around selling milk for a living.",
        "price": 1_000,
        "income": 80,
        "interval_hours": 6,
        "flavor": "oh nah bro you sold milk",
    },
    "courier": {
        "name": "uber eats delivery guy",
        "emoji": "🍔",
        "description": "deliver packages across the city. reliable, not rich.",
        "price": 4_000,
        "income": 150,
        "interval_hours": 8,
        "flavor": "another run done. your legs hurt but your wallet doesn't.",
    },
    "guard": {
        "name": "guard",
        "emoji": "🛡️",
        "description": "stand watch at the city gates. boring but steady pay.",
        "price": 8_000,
        "income": 375,
        "interval_hours": 12,
        "flavor": "shift over. nothing happened. you got paid anyway.",
    },
    "merchant": {
        "name": "merchant",
        "emoji": "🪙",
        "description": "buy low, sell high at the market. solid income.",
        "price": 25_000,
        "income": 750,
        "interval_hours": 18,
        "flavor": "the market was good today. you pocket the margin.",
    },
    "advisor": {
        "name": "vlad advisor",
        "emoji": "📜",
        "description": "counsel the crown on matters of the state.",
        "price": 40_000,
        "income": 1_000,
        "interval_hours": 24,
        "flavor": "the king took your advice. you were compensated accordingly.",
    },
    "banker": {
        "name": "vlad banker",
        "emoji": "🏦",
        "description": "manage the royal treasury. highest pay, longest wait.",
        "price": 90_000,
        "income": 3_000,
        "interval_hours": 48,
        "flavor": "the ledgers are balanced. your cut is substantial.",
    },
}


async def setup(bot):
    await bot.add_cog(EconomyCommands(bot))