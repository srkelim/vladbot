import discord
from discord.ext import commands, tasks
import asyncio
import random
import datetime
import math
from typing import Optional

from db import db
from config import QUID_EMOJI

SPECIES: dict[str, dict] = {
    "cat": {
        "emoji": "🐱", "name": "cat",
        "rarity": "common",
        "description": "aloof",
        "base_hp": 80, "base_atk": 12, "base_spd": 18,
        "specialty": "dodge", 
        "adoptable": True, "wild": True,
    },
    "dog": {
        "emoji": "🐶", "name": "dog",
        "rarity": "common",
        "description": "loyal to a fault",
        "base_hp": 100, "base_atk": 15, "base_spd": 14,
        "specialty": "tank",
        "adoptable": True, "wild": True,
    },
    "rabbit": {
        "emoji": "🐰", "name": "rabbit",
        "rarity": "common",
        "description": "bugs bunny reference",
        "base_hp": 60, "base_atk": 8, "base_spd": 25,
        "specialty": "speed",
        "adoptable": True, "wild": True,
    },
    "frog": {
        "emoji": "🐸", "name": "frog",
        "rarity": "uncommon",
        "description": "mr. frog from smiling friends",
        "base_hp": 70, "base_atk": 14, "base_spd": 16,
        "specialty": "poison",
        "adoptable": True, "wild": True,
    },
    "fox": {
        "emoji": "🦊", "name": "fox",
        "rarity": "uncommon",
        "description": "zootopia reference",
        "base_hp": 75, "base_atk": 16, "base_spd": 20,
        "specialty": "crit",
        "adoptable": True, "wild": True,
    },
    "owl": {
        "emoji": "🦉", "name": "owl",
        "rarity": "uncommon",
        "description": "king owl wysd",
        "base_hp": 65, "base_atk": 18, "base_spd": 14,
        "specialty": "crit",
        "adoptable": True, "wild": False,
    },
    "penguin": {
        "emoji": "🐧", "name": "penguin",
        "rarity": "rare",
        "description": "penguin with a tuxedo",
        "base_hp": 90, "base_atk": 13, "base_spd": 10,
        "specialty": "tank",
        "adoptable": True, "wild": False,
    },
    "wolf": {
        "emoji": "🐺", "name": "wolf",
        "rarity": "rare",
        "description": "not domesticated",
        "base_hp": 110, "base_atk": 22, "base_spd": 18,
        "specialty": "pack",
        "adoptable": False, "wild": True,
    },
    "dragon": {
        "emoji": "🦐", "name": "shrimp",
        "rarity": "legendary",
        "description": "shrimp",
        "base_hp": 160, "base_atk": 35, "base_spd": 22,
        "specialty": "fire",
        "adoptable": False, "wild": True,
    },
    "ghost_cat": {
        "emoji": "👻", "name": "casper the ghost",
        "rarity": "legendary",
        "description": "he is a pet",
        "base_hp": 50, "base_atk": 30, "base_spd": 30,
        "specialty": "dodge",
        "adoptable": False, "wild": True,
    },
}

RARITY_WEIGHTS = {
    "common":    50,
    "uncommon":  30,
    "rare":      15,
    "legendary":  5,
}

SHELTER_SPECIES = [sid for sid, s in SPECIES.items() if s["adoptable"]]
WILD_SPECIES    = [sid for sid, s in SPECIES.items() if s["wild"]]

PET_SHOP_ITEMS: dict[str, dict] = {
    "kibble": {
        "category": "food",
        "emoji": "🥣", "name": "kibble",
        "price": 20,
        "description": "basic dry food, fills hunger by 30",
        "hunger_restore": 30, "happiness_bonus": 0,
    },
    "premium_meal": {
        "category": "food",
        "emoji": "🍖", "name": "premium meal",
        "price": 60,
        "description": "a proper meal, fills hunger by 60, +10 happiness.",
        "hunger_restore": 60, "happiness_bonus": 10,
    },
    "treat": {
        "category": "food",
        "emoji": "🍬", "name": "treat",
        "price": 35,
        "description": "purely for happiness, +25 happiness, no hunger.",
        "hunger_restore": 0, "happiness_bonus": 25,
    },
    "royal_feast": {
        "category": "food",
        "emoji": "👑", "name": "royal feast",
        "price": 150,
        "description": "fills hunger fully, +30 happiness, +50 xp.",
        "hunger_restore": 100, "happiness_bonus": 30, "xp_bonus": 50,
    },
    "bandage": {
        "category": "medicine",
        "emoji": "🩹", "name": "bandage",
        "price": 40,
        "description": "restores 25 health.",
        "health_restore": 25,
    },
    "potion": {
        "category": "medicine",
        "emoji": "🧪", "name": "health potion",
        "price": 100,
        "description": "restores 60 health.",
        "health_restore": 60,
    },
    "elixir": {
        "category": "medicine",
        "emoji": "✨", "name": "elixir",
        "price": 300,
        "description": "fully restores health and +20 happiness.",
        "health_restore": 100, "happiness_bonus": 20,
    },
    "ball": {
        "category": "toy",
        "emoji": "🎾", "name": "ball",
        "price": 30,
        "description": "a toy. +20 happiness when used.",
        "happiness_bonus": 20,
    },
    "rope": {
        "category": "toy",
        "emoji": "🪢", "name": "rope toy",
        "price": 25,
        "description": "+15 happiness, +20 xp gain.",
        "happiness_bonus": 15, "xp_bonus": 20,
    },
    "puzzle": {
        "category": "toy",
        "emoji": "🧩", "name": "puzzle toy",
        "price": 80,
        "description": "+10 happiness, +80 xp. stimulating.",
        "happiness_bonus": 10, "xp_bonus": 80,
    },
    "bow": {
        "category": "outfit",
        "emoji": "🎀", "name": "bow",
        "price": 50,
        "description": "adorable isn't it",
    },
    "crown_hat": {
        "category": "outfit",
        "emoji": "👑", "name": "tiny crown",
        "price": 200,
        "description": "royal headwear",
    },
    "cape": {
        "category": "outfit",
        "emoji": "🦸", "name": "hero cape",
        "price": 175,
        "description": "your pet is now a superhero",
    },
    "glasses": {
        "category": "outfit",
        "emoji": "🕶️", "name": "sunglasses",
        "price": 90,
        "description": "too cool for you",
    },
    "armor": {
        "category": "outfit",
        "emoji": "🛡️", "name": "battle armor",
        "price": 500,
        "description": "+10 base hp in battles.",
        "battle_hp_bonus": 10,
    },
    "collar_gold": {
        "category": "accessory",
        "emoji": "📿", "name": "golden collar",
        "price": 300,
        "description": "+5 attack in battles AND looks great.",
        "battle_atk_bonus": 5,
    },
    "bell": {
        "category": "accessory",
        "emoji": "🔔", "name": "bell",
        "price": 40,
        "description": "jingle bells",
    },
    "lucky_charm": {
        "category": "accessory",
        "emoji": "🍀", "name": "lucky charm",
        "price": 250,
        "description": "+5% crit chance in battles.",
        "battle_crit_bonus": 0.05,
    },
}

TRICKS: dict[str, dict] = {
    "sit":      {"emoji": "🪑", "level_req": 1,  "xp_cost": 10,  "desc": "sit on command."},
    "shake":    {"emoji": "🤝", "level_req": 2,  "xp_cost": 15,  "desc": "shake paws."},
    "roll":     {"emoji": "🔄", "level_req": 3,  "xp_cost": 20,  "desc": "roll over."},
    "speak":    {"emoji": "🗣️", "level_req": 4,  "xp_cost": 25,  "desc": "make noise on cue."},
    "fetch":    {"emoji": "🎾", "level_req": 5,  "xp_cost": 30,  "desc": "retrieve thrown items."},
    "spin":     {"emoji": "💫", "level_req": 6,  "xp_cost": 35,  "desc": "spin in a circle."},
    "play_dead":{"emoji": "💀", "level_req": 8,  "xp_cost": 50,  "desc": "play dead."},
    "backflip": {"emoji": "🤸", "level_req": 10, "xp_cost": 75,  "desc": "a full backflip."},
    "summon":   {"emoji": "⚡", "level_req": 15, "xp_cost": 150, "desc": "appear from thin air."},
    "time_stop":{"emoji": "⏱️", "level_req": 20, "xp_cost": 300, "desc": "freeze time."},
}

MAX_PET_LEVEL = 30

def xp_for_level(level: int) -> int:
    return int(35 * (level ** 1.35))

def total_xp_for_level(level: int) -> int:
    return sum(xp_for_level(i) for i in range(2, level + 1))

def level_from_xp(xp: int) -> int:
    lvl = 1
    while lvl < MAX_PET_LEVEL and xp >= total_xp_for_level(lvl + 1):
        lvl += 1
    return lvl

def xp_progress(xp: int) -> tuple[int, int, int]:
    """Returns (current_level, xp_into_level, xp_needed_for_next)."""
    lvl = level_from_xp(xp)
    if lvl >= MAX_PET_LEVEL:
        return lvl, 0, 0
    already = total_xp_for_level(lvl)
    needed  = xp_for_level(lvl + 1)
    return lvl, xp - already, needed

def compute_stats(row: dict, inv_rows: list[dict]) -> dict:
    """Compute battle stats from pet row + inventory items."""
    species = SPECIES.get(row["species"], {})
    lvl     = row["level"]
    scale   = 1 + (lvl - 1) * 0.05

    hp  = int(species.get("base_hp",  80) * scale)
    atk = int(species.get("base_atk", 12) * scale)
    spd = int(species.get("base_spd", 15) * scale)
    crit_chance = 0.10

    if row["happiness"] >= 80:
        atk = int(atk * 1.10)
    elif row["happiness"] < 30:
        atk = int(atk * 0.80)

    spec = species.get("specialty", "")
    if spec == "pack" and row["happiness"] >= 70:
        atk = int(atk * 1.12)
    if spec == "fire":
        atk = int(atk * 1.10)

    owned_ids = {r["item_id"] for r in inv_rows if r["quantity"] > 0}
    outfit    = row.get("outfit")
    accessory = row.get("accessory")

    for slot_id in [outfit, accessory]:
        if not slot_id:
            continue
        item = PET_SHOP_ITEMS.get(slot_id, {})
        hp  += item.get("battle_hp_bonus",   0)
        atk += item.get("battle_atk_bonus",  0)
        crit_chance += item.get("battle_crit_bonus", 0.0)

    return {"hp": hp, "max_hp": hp, "atk": atk, "spd": spd, "crit": crit_chance, "spec": spec}


def battle_round(attacker_stats: dict, defender_stats: dict) -> tuple[int, bool, str]:
    """Returns (damage, is_crit, flavor_text)."""
    base   = attacker_stats["atk"]
    crit   = random.random() < attacker_stats["crit"]
    damage = int(base * (1.5 if crit else 1.0) * random.uniform(0.85, 1.15))

    spec = attacker_stats.get("spec", "")
    note = ""
    if spec == "poison" and random.random() < 0.25:
        damage += 5
        note = " *(poison)*"
    elif spec == "fire" and random.random() < 0.30:
        damage += int(base * 0.20)
        note = " *(burn)*"
    elif spec == "dodge" and random.random() < 0.20:
        damage = 0
        return 0, False, "*(dodged!)*"

    return damage, crit, ("⚡ *critical!*" + note) if crit else note

HUNGER_DECAY_PER_HOUR = 3
HAPPINESS_DECAY_PER_HOUR = 2
HEALTH_DAMAGE_WHEN_STARVING = 5
WILD_COOLDOWN_HOURS = 1

async def get_pet(user_id: int) -> dict | None:
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM pets WHERE user_id=$1", user_id)
    return dict(row) if row else None


async def get_pet_inv(user_id: int) -> list[dict]:
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("SELECT item_id, quantity FROM pet_inventory WHERE user_id=$1", user_id)
    return [dict(r) for r in rows]


def stat_bar(value: int, max_val: int = 100, length: int = 10) -> str:
    filled = round((value / max_val) * length)
    return "█" * filled + "░" * (length - filled)


def rarity_emoji(rarity: str) -> str:
    return {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "legendary": "🟡"}.get(rarity, "⚪")


async def _fire(bot, member, achievement_id: str):
    try:
        await bot.achievement_manager.unlock(user=member, achievement_id=achievement_id)
    except Exception:
        pass


async def _progress(bot, member, achievement_id: str, amount: int = 1):
    try:
        await bot.achievement_manager.increment_progress(user=member, achievement_id=achievement_id, amount=amount)
    except Exception:
        pass


async def add_pet_xp(bot, user_id: int, amount: int, member):
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT xp, level, skill_xp FROM pets WHERE user_id=$1", user_id)
        if not row:
            return 0, 0, False

        new_xp = row["xp"] + amount
        new_skill_xp = row["skill_xp"] + amount
        new_lvl = min(level_from_xp(new_xp), MAX_PET_LEVEL)

        await conn.execute(
            "UPDATE pets SET xp=$1, skill_xp=$2, level=$3 WHERE user_id=$4",
            new_xp, new_skill_xp, new_lvl, user_id
        )

    if new_lvl >= 10:
        await _fire(bot, member, "pets.level_10")
    if new_lvl >= 20:
        await _fire(bot, member, "pets.level_20")
    if new_lvl >= 30:
        await _fire(bot, member, "pets.max_level")

    return new_xp, new_lvl, new_lvl > row["level"]

class AdoptSpeciesView(discord.ui.View):
    def __init__(self, bot, member: discord.Member, available: list[str]):
        super().__init__(timeout=60)
        self.bot    = bot
        self.member = member
        for sid in available[:5]:
            sp = SPECIES[sid]
            btn = discord.ui.Button(
                label=f"{sp['emoji']} {sp['name']}",
                style=discord.ButtonStyle.primary,
                custom_id=sid
            )
            btn.callback = self._make_cb(sid)
            self.add_item(btn)

    def _make_cb(self, sid: str):
        async def cb(interaction: discord.Interaction):
            if interaction.user.id != self.member.id:
                return await interaction.response.send_message("not your adoption", ephemeral=True)
            self.stop()
            await interaction.response.defer()
            cog: PetCommands = interaction.client.cogs.get("PetCommands")
            if cog:
                await cog._finish_adopt(interaction.channel, self.member, sid, from_wild=False)
        return cb


class NameModal(discord.ui.Modal, title="name your pet"):
    pet_name = discord.ui.TextInput(
        label="what will you call them?",
        placeholder="enter a name...",
        min_length=1,
        max_length=32
    )

    def __init__(self, bot, member, species_id: str, from_wild: bool, channel):
        super().__init__()
        self.bot        = bot
        self.member     = member
        self.species_id = species_id
        self.from_wild  = from_wild
        self.channel    = channel

    async def on_submit(self, interaction: discord.Interaction):
        name = self.pet_name.value.strip()
        sp   = SPECIES[self.species_id]
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pets
                    (user_id, species, name, level, xp, hunger, happiness, health,
                     age_days, adopted_at, is_wild, tricks_learned)
                VALUES ($1,$2,$3,1,0,100,100,100,0,NOW(),$4,'{}')
                ON CONFLICT (user_id) DO NOTHING
                """,
                self.member.id, self.species_id, name, self.from_wild
            )

        await interaction.response.send_message(embed=discord.Embed(
            title=f"{sp['emoji']} welcome, {name}!",
            description=(
                f"**{self.member.display_name}** adopted a **{sp['name']}**!\n\n"
                f"*{sp['description']}*\n\n"
                "use `!pet` to view them, `!feed` to feed them, `!play` to play games with them."
            ),
            color=discord.Color.green()
        ))

        await _fire(self.bot, self.member, "pets.first_adopt")
        if self.from_wild:
            await _fire(self.bot, self.member, "pets.wild_tamed")
        sp_data = SPECIES[self.species_id]
        if sp_data["rarity"] == "legendary":
            await _fire(self.bot, self.member, "pets.legendary_adopt")

class WildEncounterView(discord.ui.View):
    def __init__(self, bot, member: discord.Member, species_id: str):
        super().__init__(timeout=30)
        self.bot        = bot
        self.member     = member
        self.species_id = species_id

    @discord.ui.button(label="🤲 approach", style=discord.ButtonStyle.success)
    async def approach(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.member.id:
            return await interaction.response.send_message("not your encounter", ephemeral=True)
        self.stop()
        existing = await get_pet(self.member.id)
        if existing and not existing["is_dead"]:
            await interaction.response.edit_message(
                content="you already have a pet. you can't take in another wild one.",
                embed=None, view=None
            )
            return
        await interaction.response.send_modal(
            NameModal(self.bot, self.member, self.species_id, from_wild=True, channel=interaction.channel)
        )

    @discord.ui.button(label="🏃 flee", style=discord.ButtonStyle.secondary)
    async def flee(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.member.id:
            return await interaction.response.send_message("not your encounter", ephemeral=True)
        self.stop()
        sp = SPECIES[self.species_id]
        await interaction.response.edit_message(
            content=f"*the {sp['emoji']} {sp['name']} watches you leave.*",
            embed=None, view=None
        )

class BuyModal(discord.ui.Modal, title="how many"):
    quantity = discord.ui.TextInput(
        label="quantity",
        placeholder="enter a number",
        default="1",
        min_length=1,
        max_length=4,
    )

    def __init__(self, bot, member: discord.Member, item_id: str, item: dict):
        super().__init__()
        self.bot     = bot
        self.member  = member
        self.item_id = item_id
        self.item    = item

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qty = int(self.quantity.value.strip())
            if qty < 1:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "enter a valid positive number.", ephemeral=True
            )

        total = self.item["price"] * qty

        async with db.pool.acquire() as conn:
            wallet = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id=$1", self.member.id
            ) or 0

            if wallet < total:
                can_afford = wallet // self.item["price"]
                return await interaction.response.send_message(
                    f"❌ **{qty}x {self.item['name']}** costs **{total}** {QUID_EMOJI} "
                    f"but you only have **{wallet}**."
                    + (f" you can afford **{can_afford}**." if can_afford > 0 else ""),
                    ephemeral=True
                )

            await conn.execute(
                "UPDATE economy SET quid=quid-$1 WHERE user_id=$2",
                total, self.member.id
            )
            await conn.execute(
                """
                INSERT INTO pet_inventory (user_id, item_id, quantity)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, item_id)
                DO UPDATE SET quantity = pet_inventory.quantity + $3
                """,
                self.member.id, self.item_id, qty
            )

        await interaction.response.send_message(
            f"✅ bought **{qty}x {self.item['emoji']} {self.item['name']}** "
            f"for **{total}** {QUID_EMOJI}!\n"
            f"use `!puse {self.item_id}` or `!puse {self.item_id} <qty>` to use them.",
            ephemeral=True
        )
        await _fire(self.bot, self.member, "pets.first_purchase")

class PetShopView(discord.ui.View):
    CATEGORIES = ["food", "medicine", "toy", "outfit", "accessory"]

    def __init__(self, bot, member: discord.Member):
        super().__init__(timeout=60)
        self.bot     = bot
        self.member  = member
        self.cat_idx = 0
        self._rebuild()

    def _items_in_cat(self) -> list[tuple[str, dict]]:
        cat = self.CATEGORIES[self.cat_idx]
        return [(iid, i) for iid, i in PET_SHOP_ITEMS.items() if i["category"] == cat]

    def _rebuild(self):
        self.clear_items()
        for iid, item in self._items_in_cat()[:5]:
            btn = discord.ui.Button(
                label=f"{item['emoji']} {item['name']}",
                style=discord.ButtonStyle.primary
            )
            btn.callback = self._buy_cb(iid, item)
            self.add_item(btn)
        prev = discord.ui.Button(label="◀", style=discord.ButtonStyle.success)
        nxt  = discord.ui.Button(label="▶", style=discord.ButtonStyle.success)
        prev.callback = self._nav(-1)
        nxt.callback  = self._nav(+1)
        self.add_item(prev)
        self.add_item(nxt)

    def _embed(self) -> discord.Embed:
        cat   = self.CATEGORIES[self.cat_idx]
        items = self._items_in_cat()
        embed = discord.Embed(
            title=f"🛒 pet shop - {cat}",
            color=discord.Color.blurple()
        )
        for _, item in items[:5]:
            embed.add_field(
                name=f"{item['emoji']} **{item['name']}** - {item['price']} {QUID_EMOJI}",
                value=item["description"],
                inline=False
            )
        embed.set_footer(text=f"category {self.cat_idx+1}/{len(self.CATEGORIES)} • click an item to buy")
        return embed

    def _buy_cb(self, iid: str, item: dict):
        async def cb(interaction: discord.Interaction):
            if interaction.user.id != self.member.id:
                return await interaction.response.send_message("not your shop", ephemeral=True)
            await interaction.response.send_modal(BuyModal(self.bot, self.member, iid, item))
        return cb

    def _nav(self, direction: int):
        async def cb(interaction: discord.Interaction):
            if interaction.user.id != self.member.id:
                return await interaction.response.send_message("not your shop", ephemeral=True)
            self.cat_idx = (self.cat_idx + direction) % len(self.CATEGORIES)
            self._rebuild()
            await interaction.response.edit_message(embed=self._embed(), view=self)
        return cb


class TrickView(discord.ui.View):
    def __init__(self, bot, member: discord.Member, pet_row: dict):
        super().__init__(timeout=30)
        self.bot     = bot
        self.member  = member
        self.pet_row = pet_row
        learned = pet_row.get("tricks_learned") or []
        for tid in learned[:5]:
            trick = TRICKS.get(tid)
            if not trick:
                continue
            btn = discord.ui.Button(label=f"{trick['emoji']} {tid}", style=discord.ButtonStyle.primary)
            btn.callback = self._perform_cb(tid, trick)
            self.add_item(btn)

    def _perform_cb(self, tid: str, trick: dict):
        async def cb(interaction: discord.Interaction):
            if interaction.user.id != self.member.id:
                return await interaction.response.send_message("not your pet", ephemeral=True)
            self.stop()
            sp = SPECIES.get(self.pet_row["species"], {})
            await interaction.response.edit_message(
                content=(
                    f"{sp.get('emoji','🐾')} **{self.pet_row['name']}** performs **{tid}**! "
                    f"{trick['emoji']}\n*{trick['desc']}*"
                ),
                embed=None, view=None
            )
            await add_pet_xp(self.bot, self.member.id, 3, self.member)
        return cb


class BattleChallengeView(discord.ui.View):
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
        await interaction.response.edit_message(content="challenge declined.", view=None)

class PetCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = set()
        self.stat_decay_task.start()
        self.age_task.start()

    def cog_unload(self):
        self.stat_decay_task.cancel()
        self.age_task.cancel()

    @commands.command(name="adoptpet", aliases=["petadopt"], help="adopt a pet", usage="!adoptpet")
    async def adopt(self, ctx):
        existing = await get_pet(ctx.author.id)
        if existing and not existing["is_dead"]:
            return await ctx.send("you already have a pet. use `!release` to let them go first.")

        pool = []
        for sid in SHELTER_SPECIES:
            pool.extend([sid] * RARITY_WEIGHTS[SPECIES[sid]["rarity"]])
        picks = random.sample(list(set(pool)), min(4, len(set(pool))))

        embed = discord.Embed(
            title="🏠 the shelter",
            description=(
                "these pets are looking for a home.\n"
                "choose one to adopt. they'll be with you forever or until you release them."
            ),
            color=discord.Color.green()
        )
        for sid in picks:
            sp = SPECIES[sid]
            embed.add_field(
                name=f"{sp['emoji']} **{sp['name']}** {rarity_emoji(sp['rarity'])} {sp['rarity']}",
                value=sp["description"],
                inline=False
            )
        await ctx.send(embed=embed, view=AdoptSpeciesView(self.bot, ctx.author, picks))

    async def _finish_adopt(self, channel, member: discord.Member, species_id: str, from_wild: bool):
        sp = SPECIES[species_id]
        await channel.send(
            embed=discord.Embed(
                description=f"{sp['emoji']} what will you name your **{sp['name']}**? type a name:",
                color=discord.Color.green()
            )
        )
        def check(m): return m.author.id == member.id and m.channel == channel
        try:
            msg = await self.bot.wait_for("message", timeout=30, check=check)
        except asyncio.TimeoutError:
            return await channel.send("timed out. run `!adoptpet` again.")
        name = msg.content.strip()[:32]
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pets
                    (user_id, species, name, level, xp, hunger, happiness, health,
                     age_days, adopted_at, is_wild, tricks_learned)
                VALUES ($1,$2,$3,1,0,100,100,100,0,NOW(),$4,'{}')
                ON CONFLICT (user_id) DO UPDATE
                    SET species=$2, name=$3, level=1, xp=0, hunger=100, happiness=100,
                        health=100, age_days=0, adopted_at=NOW(), is_wild=$4,
                        is_dead=FALSE, tricks_learned='{}'
                """,
                member.id, species_id, name, from_wild
            )
        await channel.send(embed=discord.Embed(
            title=f"{sp['emoji']} welcome, {name}!",
            description=(
                f"**{member.display_name}** {'tamed' if from_wild else 'adopted'} a **{sp['name']}**!\n\n"
                f"*{sp['description']}*\n\n"
                "use `!pet` to view them, `!feed` to feed them, `!play` to play."
            ),
            color=discord.Color.green()
        ))
        await _fire(self.bot, member, "pets.first_adopt")
        if from_wild:
            await _fire(self.bot, member, "pets.wild_tamed")
        if SPECIES[species_id]["rarity"] == "legendary":
            await _fire(self.bot, member, "pets.legendary_adopt")

    @commands.command(name="wild", aliases=["wildencounter"], help="search for a wild pet", usage="!wildencounter")
    async def wild_encounter(self, ctx):
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT last_encounter FROM pet_wild_encounters WHERE user_id=$1", ctx.author.id
            )
        if row and row["last_encounter"]:
            last = row["last_encounter"].replace(tzinfo=datetime.timezone.utc) if row["last_encounter"].tzinfo is None else row["last_encounter"]
            next_enc = last + datetime.timedelta(hours=WILD_COOLDOWN_HOURS)
            if datetime.datetime.now(datetime.timezone.utc) < next_enc:
                ts = int(next_enc.timestamp())
                return await ctx.send(f"🌿 the wild is quiet. try again <t:{ts}:R>.")

        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pet_wild_encounters (user_id, last_encounter) VALUES ($1, NOW())
                ON CONFLICT (user_id) DO UPDATE SET last_encounter=NOW()
                """,
                ctx.author.id
            )

        if random.random() < 0.40:
            flavor = random.choice([
                "you searched the area. nothing but rustling leaves.",
                "you heard something.",
                "footprints in the mud. whatever it was, it's gone.",
            ])
            return await ctx.send(f"🌿 *{flavor}*")

        pool = []
        for sid in WILD_SPECIES:
            pool.extend([sid] * RARITY_WEIGHTS[SPECIES[sid]["rarity"]])
        sid = random.choice(pool)
        sp  = SPECIES[sid]

        await ctx.send(
            embed=discord.Embed(
                title=f"{sp['emoji']} a wild {sp['name']} appears!",
                description=(
                    f"*{sp['description']}*\n\n"
                    f"**rarity:** {rarity_emoji(sp['rarity'])} {sp['rarity']}\n\n"
                    "approach carefully or flee?"
                ),
                color=discord.Color.dark_green()
            ),
            view=WildEncounterView(self.bot, ctx.author, sid)
        )

    @commands.command(name="pet", aliases=["mypet", "petprofile"], help="view your pet", usage="!pet [user]")
    async def pet_profile(self, ctx, member: Optional[discord.Member] = None):
        target = member or ctx.author
        row = await get_pet(target.id)
        if not row:
            if target == ctx.author:
                return await ctx.send("you don't have a pet. adopt one with `!adoptpet` or search with `!wild`.")
            return await ctx.send(f"**{target.display_name}** has no pet.")

        sp      = SPECIES.get(row["species"], {"emoji": "🐾", "name": row["species"], "rarity": "common"})
        lvl, xp_into, xp_needed = xp_progress(row["xp"])

        if row["is_dead"]:
            status = "💀 deceased"
        elif row["health"] < 20:
            status = "🆘 critical"
        elif row["hunger"] < 20:
            status = "😰 starving"
        elif row["happiness"] < 20:
            status = "😔 miserable"
        else:
            status = "✅ healthy"

        embed = discord.Embed(
            title=f"{sp['emoji']} {row['name']}",
            color=discord.Color.green() if not row["is_dead"] else discord.Color.dark_gray()
        )
        embed.set_author(name=f"{target.display_name}'s pet")
        embed.add_field(name="species", value=f"{sp['name']} {rarity_emoji(sp['rarity'])}", inline=True)
        embed.add_field(name="status", value=status, inline=True)
        embed.add_field(name="age", value=f"{row['age_days']} days", inline=True)

        embed.add_field(name=f"level {lvl}", value=(
            f"`{stat_bar(xp_into, max(xp_needed,1))}` {xp_into}/{xp_needed} xp"
            if lvl < MAX_PET_LEVEL else "**MAX LEVEL**"
        ), inline=False)

        embed.add_field(name="❤️ health", value=f"`{stat_bar(row['health'])}` {row['health']}/100",inline=True)
        embed.add_field(name="🍖 hunger", value=f"`{stat_bar(row['hunger'])}` {row['hunger']}/100", inline=True)
        embed.add_field(name="😊 happiness", value=f"`{stat_bar(row['happiness'])}` {row['happiness']}/100", inline=True)

        tricks = row.get("tricks_learned") or []
        if tricks:
            trick_list = " ".join(TRICKS[t]["emoji"] for t in tricks if t in TRICKS)
            embed.add_field(name=f"🎓 tricks ({len(tricks)})", value=trick_list or "-", inline=True)

        outfit    = PET_SHOP_ITEMS.get(row.get("outfit")    or "", {})
        accessory = PET_SHOP_ITEMS.get(row.get("accessory") or "", {})
        equipped  = " ".join(filter(None, [
            f"{outfit.get('emoji','')} {outfit.get('name','')}"    if outfit    else "",
            f"{accessory.get('emoji','')} {accessory.get('name','')}" if accessory else "",
        ])) or "none"
        embed.add_field(name="👗 equipped",  value=equipped, inline=True)

        bw, bl = row["battles_won"], row["battles_lost"]
        embed.add_field(name="⚔️ battles", value=f"{bw}W / {bl}L", inline=True)

        embed.set_footer(text=f"origin: {'wild' if row['is_wild'] else 'shelter'}")
        await ctx.send(embed=embed)

    @commands.command(name="feed", aliases=["pfeed"], help="feed your pet", usage="!feed [item_id] [qty]")
    async def pfeed(self, ctx, item_id: Optional[str] = None, qty: int = 1):
        if qty < 1:
            return await ctx.send("quantity must be at least 1.")
        row = await get_pet(ctx.author.id)
        if not row or row["is_dead"]:
            return await ctx.send("you don't have a living pet.")

        inv = await get_pet_inv(ctx.author.id)

        if item_id is None:
            for r in inv:
                candidate = PET_SHOP_ITEMS.get(r["item_id"])
                if candidate and candidate.get("category") == "food" and r["quantity"] > 0:
                    item_id = r["item_id"]
                    break
            if item_id is None:
                return await ctx.send("you have no food. buy some with `!petshop`.")

        item = PET_SHOP_ITEMS.get(item_id)
        if not item or item.get("category") != "food":
            return await ctx.send(f"**{item_id}** is not a food item.")

        async with db.pool.acquire() as conn:
            owned = await conn.fetchval(
                "SELECT quantity FROM pet_inventory WHERE user_id=$1 AND item_id=$2",
                ctx.author.id, item_id
            ) or 0
            if owned < qty:
                return await ctx.send(
                    f"you only have **{owned}x {item['name']}** (need {qty})."
                )
            new_qty = owned - qty
            if new_qty <= 0:
                await conn.execute(
                    "DELETE FROM pet_inventory WHERE user_id=$1 AND item_id=$2",
                    ctx.author.id, item_id
                )
            else:
                await conn.execute(
                    "UPDATE pet_inventory SET quantity=$1 WHERE user_id=$2 AND item_id=$3",
                    new_qty, ctx.author.id, item_id
                )

            new_hunger    = min(100, row["hunger"]    + item.get("hunger_restore",  0) * qty)
            new_happiness = min(100, row["happiness"] + item.get("happiness_bonus", 0) * qty)
            xp_bonus      = item.get("xp_bonus", 0) * qty

            await conn.execute(
                "UPDATE pets SET hunger=$1, happiness=$2, last_fed=NOW() WHERE user_id=$3",
                new_hunger, new_happiness, ctx.author.id
            )

        sp  = SPECIES.get(row["species"], {})
        msg = (
            f"{sp.get('emoji','🐾')} **{row['name']}** ate **{qty}x {item['emoji']} {item['name']}**!\n"
            f"hunger: `{stat_bar(new_hunger)}` {new_hunger}/100"
        )
        if item.get("happiness_bonus"):
            msg += f" | happiness: `{stat_bar(new_happiness)}` {new_happiness}/100"
        await ctx.send(msg)

        if xp_bonus:
            _, new_lvl, leveled = await add_pet_xp(self.bot, ctx.author.id, xp_bonus, ctx.author)
            if leveled:
                await ctx.send(f"✨ **{row['name']}** levelled up to **level {new_lvl}**!")
        await _fire(self.bot, ctx.author, "pets.first_feed")

    @commands.command(name="play", aliases=["pplay"], help="play with your pet", usage="!play [item_id] [qty]")
    async def pplay(self, ctx, item_id: Optional[str] = None, qty: int = 1):
        if qty < 1:
            return await ctx.send("quantity must be at least 1.")
        row = await get_pet(ctx.author.id)
        if not row or row["is_dead"]:
            return await ctx.send("you don't have a living pet.")

        if item_id is None and row["last_played"]:
            last = row["last_played"]
            if last.tzinfo is None:
                last = last.replace(tzinfo=datetime.timezone.utc)
            secs = (datetime.datetime.now(datetime.timezone.utc) - last).total_seconds()
            if secs < 3600:
                ts = int((last + datetime.timedelta(hours=1)).timestamp())
                return await ctx.send(f"😴 **{row['name']}** needs to rest. play again <t:{ts}:R>.")

        hap_gain = 20 * qty
        xp_gain  = 50 * qty
        used_item = None

        if item_id:
            item = PET_SHOP_ITEMS.get(item_id)
            if not item or item.get("category") != "toy":
                return await ctx.send(f"**{item_id}** is not a toy.")
            async with db.pool.acquire() as conn:
                owned = await conn.fetchval(
                    "SELECT quantity FROM pet_inventory WHERE user_id=$1 AND item_id=$2",
                    ctx.author.id, item_id
                ) or 0
                if owned < qty:
                    return await ctx.send(
                        f"you only have **{owned}x {item['name']}** (need {qty})."
                    )
                new_qty = owned - qty
                if new_qty <= 0:
                    await conn.execute(
                        "DELETE FROM pet_inventory WHERE user_id=$1 AND item_id=$2",
                        ctx.author.id, item_id
                    )
                else:
                    await conn.execute(
                        "UPDATE pet_inventory SET quantity=$1 WHERE user_id=$2 AND item_id=$3",
                        new_qty, ctx.author.id, item_id
                    )
            hap_gain += item.get("happiness_bonus", 0) * qty
            xp_gain  += item.get("xp_bonus",        0) * qty
            used_item = item

        new_hap = min(100, row["happiness"] + hap_gain)
        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE pets SET happiness=$1, last_played=NOW() WHERE user_id=$2",
                new_hap, ctx.author.id
            )

        sp  = SPECIES.get(row["species"], {})
        msg = f"{sp.get('emoji','🐾')} you played with **{row['name']}**"
        if used_item:
            msg += f" using **{qty}x {used_item['emoji']} {used_item['name']}**"
        msg += f"!\nhappiness: `{stat_bar(new_hap)}` {new_hap}/100"
        await ctx.send(msg)

        result = await add_pet_xp(self.bot, ctx.author.id, xp_gain, ctx.author)
        if result:
            _, new_lvl, leveled = result
            if leveled:
                await ctx.send(f"✨ **{row['name']}** levelled up to **level {new_lvl}**!")

    @commands.command(name="heal", aliases=["pheal"], help="heal your pet", usage="!heal <item_id> [qty]")
    async def pheal(self, ctx, item_id: str, qty: int = 1):
        if qty < 1:
            return await ctx.send("quantity must be at least 1.")
        row = await get_pet(ctx.author.id)
        if not row or row["is_dead"]:
            return await ctx.send("you don't have a living pet.")

        item = PET_SHOP_ITEMS.get(item_id)
        if not item or item.get("category") != "medicine":
            return await ctx.send(f"**{item_id}** is not a medicine item. try `bandage`, `potion`, or `elixir`.")

        async with db.pool.acquire() as conn:
            owned = await conn.fetchval(
                "SELECT quantity FROM pet_inventory WHERE user_id=$1 AND item_id=$2",
                ctx.author.id, item_id
            ) or 0
            if owned < qty:
                return await ctx.send(
                    f"you only have **{owned}x {item['name']}** (need {qty})."
                )
            new_qty = owned - qty
            if new_qty <= 0:
                await conn.execute(
                    "DELETE FROM pet_inventory WHERE user_id=$1 AND item_id=$2",
                    ctx.author.id, item_id
                )
            else:
                await conn.execute(
                    "UPDATE pet_inventory SET quantity=$1 WHERE user_id=$2 AND item_id=$3",
                    new_qty, ctx.author.id, item_id
                )
            new_health    = min(100, row["health"]    + item.get("health_restore",  0) * qty)
            new_happiness = min(100, row["happiness"] + item.get("happiness_bonus", 0) * qty)
            await conn.execute(
                "UPDATE pets SET health=$1, happiness=$2 WHERE user_id=$3",
                new_health, new_happiness, ctx.author.id
            )

        sp = SPECIES.get(row["species"], {})
        await ctx.send(
            f"{sp.get('emoji','🐾')} **{row['name']}** used **{qty}x {item['emoji']} {item['name']}**!\n"
            f"health: `{stat_bar(new_health)}` {new_health}/100"
        )
        await _fire(self.bot, ctx.author, "pets.healed_pet")

    @commands.command(name="train", aliases=["ptrain"], help="train your pet (xp)", usage="!train")
    async def ptrain(self, ctx):
        row = await get_pet(ctx.author.id)
        if not row or row["is_dead"]:
            return await ctx.send("you don't have a living pet.")
        if row["last_trained"]:
            last = row["last_trained"].replace(tzinfo=datetime.timezone.utc) if row["last_trained"].tzinfo is None else row["last_trained"]
            secs = (datetime.datetime.now(datetime.timezone.utc) - last).total_seconds()
            if secs < 43200:
                ts = int((last + datetime.timedelta(hours=12)).timestamp())
                return await ctx.send(f"🏋️ **{row['name']}** is still recovering. train again <t:{ts}:R>.")

        xp_gain = random.randint(75, 100)
        async with db.pool.acquire() as conn:
            await conn.execute("UPDATE pets SET last_trained=NOW() WHERE user_id=$1", ctx.author.id)

        result = await add_pet_xp(self.bot, ctx.author.id, xp_gain, ctx.author)
        sp = SPECIES.get(row["species"], {})
        await ctx.send(
            f"🏋️ **{row['name']}** trained hard and earned **+{xp_gain} xp**!"
            + (f"\n✨ levelled up to **{result[1]}**!" if result and result[2] else "")
        )

    @commands.command(name="teach", aliases=["pteach"], help="teach your pet a trick", usage="!teach <trick>")
    async def pteach(self, ctx, trick_id: str):
        trick_id = trick_id.lower()
        trick    = TRICKS.get(trick_id)
        if not trick:
            available = ", ".join(f"`{t}`" for t in TRICKS)
            return await ctx.send(f"unknown trick. available: {available}")

        row = await get_pet(ctx.author.id)
        if not row or row["is_dead"]:
            return await ctx.send("you don't have a living pet.")
        if row["level"] < trick["level_req"]:
            return await ctx.send(
                f"**{row['name']}** needs to be **level {trick['level_req']}** to learn `{trick_id}`. "
                f"currently level {row['level']}."
            )
        tricks_learned = row.get("tricks_learned") or []
        if trick_id in tricks_learned:
            return await ctx.send(f"**{row['name']}** already knows `{trick_id}`.")

        if row["xp"] < trick["xp_cost"]:
            return await ctx.send(
                f"**{row['name']}** needs **{trick['xp_cost']} xp** to learn this. "
                f"they have **{row['xp']}**."
            )

        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE pets SET skill_xp = skill_xp - $1, tricks_learned = array_append(tricks_learned,$2) WHERE user_id=$3",
                trick["xp_cost"], trick_id, ctx.author.id
            )

        sp = SPECIES.get(row["species"], {})
        await ctx.send(
            f"{trick['emoji']} **{row['name']}** learned **{trick_id}**!\n*{trick['desc']}*"
        )
        await _fire(self.bot, ctx.author, "pets.first_trick")
        if len(tricks_learned) + 1 >= len(TRICKS):
            await _fire(self.bot, ctx.author, "pets.all_tricks")

    @commands.command(name="tricks", aliases=["ptricks"], help="see your pets tricks", usage="!tricks")
    async def ptricks(self, ctx):
        row = await get_pet(ctx.author.id)
        if not row or row["is_dead"]:
            return await ctx.send("you don't have a living pet.")
        learned = row.get("tricks_learned") or []
        sp = SPECIES.get(row["species"], {})
        embed = discord.Embed(
            title=f"{sp.get('emoji','🐾')} {row['name']}'s tricks",
            color=discord.Color.blurple()
        )
        for tid, trick in TRICKS.items():
            known  = tid in learned
            prefix = "✅" if known else f"🔒 lvl {trick['level_req']}"
            embed.add_field(
                name=f"{prefix} {trick['emoji']} {tid}",
                value=trick["desc"],
                inline=True
            )
        if learned:
            embed.set_footer(text="use !perform to show off a trick")
        await ctx.send(embed=embed, view=TrickView(self.bot, ctx.author, row) if learned else discord.utils.MISSING)

    @commands.command(name="perform", help="perform a trick your pet knows", usage="!perform <trick>")
    async def perform(self, ctx, trick_id: str):
        trick_id = trick_id.lower()
        trick    = TRICKS.get(trick_id)
        if not trick:
            return await ctx.send("unknown trick.")
        row = await get_pet(ctx.author.id)
        if not row or row["is_dead"]:
            return await ctx.send("you don't have a living pet.")
        if trick_id not in (row.get("tricks_learned") or []):
            return await ctx.send(f"**{row['name']}** doesn't know `{trick_id}`. teach them with `!teach`.")
        sp = SPECIES.get(row["species"], {})
        await ctx.send(
            f"{sp.get('emoji','🐾')} **{row['name']}** performs **{trick_id}**! {trick['emoji']}\n*{trick['desc']}*"
        )
        await add_pet_xp(self.bot, ctx.author.id, 3, ctx.author)

    @commands.command(name="petshop", aliases=["pshop"], help="browse the pet shop", usage="!petshop")
    async def petshop(self, ctx):
        view = PetShopView(self.bot, ctx.author)
        await ctx.send(embed=view._embed(), view=view)

    @commands.command(name="inv", aliases=["petinv", "petbag"], help="view your pet item inventory", usage="!inv")
    async def pinv(self, ctx):
        inv = await get_pet_inv(ctx.author.id)
        if not inv:
            return await ctx.send("your pet bag is empty. buy items at `!petshop`.")
        embed = discord.Embed(title="🎒 pet inventory", color=discord.Color.blurple())
        for r in inv:
            item = PET_SHOP_ITEMS.get(r["item_id"], {"emoji": "📦", "name": r["item_id"]})
            embed.add_field(
                name=f"{item.get('emoji','📦')} {item.get('name', r['item_id'])}",
                value=f"x{r['quantity']}",
                inline=True
            )
        embed.set_footer(text="use !puse <item_id> to use an item | !equip <item_id> for cosmetics")
        await ctx.send(embed=embed)

    @commands.command(name="puse", help="use a pet item", usage="!puse <item_id> [qty]")
    async def puse(self, ctx, item_id: str, qty: int = 1):
        item = PET_SHOP_ITEMS.get(item_id)
        if not item:
            return await ctx.send(f"unknown item `{item_id}`.")
        cat = item.get("category")
        if cat == "food":
            await ctx.invoke(self.pfeed, item_id=item_id, qty=qty)
        elif cat == "medicine":
            await ctx.invoke(self.pheal, item_id=item_id, qty=qty)
        elif cat == "toy":
            await ctx.invoke(self.pplay, item_id=item_id, qty=qty)
        elif cat in ("outfit", "accessory"):
            await ctx.invoke(self.pequip, item_id=item_id)
        else:
            await ctx.send(f"don't know how to use `{item_id}`.")

    @commands.command(name="equip", aliases=["pequip"], help="equip an item on your pet", usage="!equip <item_id>")
    async def pequip(self, ctx, item_id: str):
        item = PET_SHOP_ITEMS.get(item_id)
        if not item:
            return await ctx.send(f"unknown item `{item_id}`.")
        cat = item.get("category")
        if cat not in ("outfit", "accessory"):
            return await ctx.send("only outfits and accessories can be equipped.")
        inv = await get_pet_inv(ctx.author.id)
        if not any(r["item_id"] == item_id and r["quantity"] > 0 for r in inv):
            return await ctx.send(f"you don't own **{item['name']}**. buy it at `!petshop`.")
        row = await get_pet(ctx.author.id)
        if not row or row["is_dead"]:
            return await ctx.send("you don't have a living pet.")

        col = {"outfit": "outfit", "accessory": "accessory"}[cat]
        async with db.pool.acquire() as conn:
            await conn.execute(f"UPDATE pets SET {col}=$1 WHERE user_id=$2", item_id, ctx.author.id)

        sp = SPECIES.get(row["species"], {})
        await ctx.send(f"{sp.get('emoji','🐾')} **{row['name']}** equipped **{item['emoji']} {item['name']}**!")
        await _fire(self.bot, ctx.author, "pets.equipped_item")

    @commands.command(name="pbattle", aliases=["petbattle"], help="challenge someones pet", usage="!pbattle @user")
    async def pbattle(self, ctx, opponent: discord.Member):
        if opponent.bot or opponent.id == ctx.author.id:
            return await ctx.send("no.")

        pair = frozenset({ctx.author.id, opponent.id})
        if pair in self.active_battles:
            return await ctx.send("there's already an ongoing battle between you two.")

        a_row = await get_pet(ctx.author.id)
        b_row = await get_pet(opponent.id)

        if not a_row or a_row["is_dead"]:
            return await ctx.send("you don't have a living pet.")
        if not b_row or b_row["is_dead"]:
            return await ctx.send(f"**{opponent.display_name}** doesn't have a living pet.")

        view = BattleChallengeView(ctx.author, opponent)
        msg = await ctx.send(
            embed=discord.Embed(
                title="⚔️ pet battle challenge",
                description=(
                    f"**{ctx.author.display_name}**'s {SPECIES[a_row['species']]['emoji']} **{a_row['name']}**\n"
                    f"vs.\n"
                    f"**{opponent.display_name}**'s {SPECIES[b_row['species']]['emoji']} **{b_row['name']}**"
                ),
                color=discord.Color.red()
            ),
            view=view
        )

        await view.wait()
        if not view.accepted:
            return

        self.active_battles.add(pair)

        try:
            a_inv = await get_pet_inv(ctx.author.id)
            b_inv = await get_pet_inv(opponent.id)

            a_stats = compute_stats(a_row, a_inv)
            b_stats = compute_stats(b_row, b_inv)

            a_hp = a_stats["hp"]
            b_hp = b_stats["hp"]

            a_name = f"{SPECIES[a_row['species']]['emoji']} {a_row['name']}"
            b_name = f"{SPECIES[b_row['species']]['emoji']} {b_row['name']}"

            def hp_bar(cur, maxhp):
                filled = int((cur / maxhp) * 10)
                return "█" * filled + "░" * (10 - filled)

            await msg.edit(embed=discord.Embed(
                title="⚔️ battle begins!",
                description=f"{a_name} vs {b_name}",
                color=discord.Color.red()
            ), view=None)

            await asyncio.sleep(1)

            round_num = 0

            while a_hp > 0 and b_hp > 0 and round_num < 20:
                round_num += 1
                lines = [f"**round {round_num}**"]

                if a_stats["spd"] >= b_stats["spd"]:
                    order = [
                        ("a", a_name, a_stats),
                        ("b", b_name, b_stats)
                    ]
                else:
                    order = [
                        ("b", b_name, b_stats),
                        ("a", a_name, a_stats)
                    ]

                for side, name, stats in order:
                    if a_hp <= 0 or b_hp <= 0:
                        break

                    target_hp = b_hp if side == "a" else a_hp
                    target_stats = b_stats if side == "a" else a_stats
                    target_name = b_name if side == "a" else a_name

                    dmg, crit, note = battle_round(stats, target_stats)

                    if side == "a":
                        b_hp -= dmg
                    else:
                        a_hp -= dmg

                    lines.append(f"{name} → {target_name}: **{dmg}** {note}")

                lines.append(
                    f"\n{a_name}: `{hp_bar(max(a_hp,0), a_stats['hp'])}` {max(0,a_hp)}\n"
                    f"{b_name}: `{hp_bar(max(b_hp,0), b_stats['hp'])}` {max(0,b_hp)}"
                )

                await msg.edit(embed=discord.Embed(
                    title=f"⚔️ round {round_num}",
                    description="\n".join(lines),
                    color=discord.Color.red()
                ))

                await asyncio.sleep(1.2)

            if a_hp > 0:
                winner_member, loser_member = ctx.author, opponent
                winner_row, loser_row = a_row, b_row
            else:
                winner_member, loser_member = opponent, ctx.author
                winner_row, loser_row = b_row, a_row

            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE pets SET battles_won=battles_won+1 WHERE user_id=$1",
                    winner_member.id
                )
                await conn.execute(
                    "UPDATE pets SET battles_lost=battles_lost+1 WHERE user_id=$1",
                    loser_member.id
                )

                loser_health = max(10, (await get_pet(loser_member.id))["health"] - random.randint(10, 25))

                await conn.execute(
                    "UPDATE pets SET health=$1 WHERE user_id=$2",
                    loser_health, loser_member.id
                )

                await conn.execute(
                    "INSERT INTO pet_battle_log (challenger, opponent, winner) VALUES ($1,$2,$3)",
                    ctx.author.id, opponent.id, winner_member.id
                )

            w_sp = SPECIES[winner_row["species"]]

            await msg.edit(embed=discord.Embed(
                title="🏆 battle over!",
                description=(
                    f"{w_sp['emoji']} **{winner_row['name']}** wins!\n\n"
                    f"**{loser_member.display_name}**'s pet took damage."
                ),
                color=discord.Color.gold()
            ))

            xp_w = random.randint(100, 125)
            xp_l = random.randint(75, 85)

            _, wlvl, wlev = await add_pet_xp(self.bot, winner_member.id, xp_w, winner_member)
            _, llvl, llev = await add_pet_xp(self.bot, loser_member.id, xp_l, loser_member)

            if wlev:
                await ctx.send(f"✨ **{winner_row['name']}** leveled up to **{wlvl}**!")
            if llev:
                await ctx.send(f"✨ **{loser_row['name']}** leveled up to **{llvl}**!")

        finally:
            self.active_battles.discard(pair)

    @commands.command(name="rename", aliases=["renamepet"], help="rename your pet", usage="!prename <new name>")
    async def prename(self, ctx, *, new_name: str):
        row = await get_pet(ctx.author.id)
        if not row:
            return await ctx.send("you don't have a pet.")
        new_name = new_name.strip()[:32]
        async with db.pool.acquire() as conn:
            await conn.execute("UPDATE pets SET name=$1 WHERE user_id=$2", new_name, ctx.author.id)
        sp = SPECIES.get(row["species"], {})
        await ctx.send(f"{sp.get('emoji','🐾')} your pet is now called **{new_name}**.")

    @commands.command(name="release", help="release your pet", usage="!release")
    async def petrelease(self, ctx):
        row = await get_pet(ctx.author.id)
        if not row:
            return await ctx.send("you don't have a pet.")
        sp = SPECIES.get(row["species"], {})
        embed = discord.Embed(
            title=f"💔 release {row['name']}?",
            description=(
                f"are you sure you want to release **{row['name']}** the {sp.get('name','pet')}?\n\n"
                "they will return to the wild. this cannot be undone."
            ),
            color=discord.Color.red()
        )

        class ConfirmRelease(discord.ui.View):
            def __init__(self_, bot, member, row_):
                super().__init__(timeout=20)
                self_.bot    = bot
                self_.member = member
                self_.row_   = row_

            @discord.ui.button(label="release", style=discord.ButtonStyle.danger)
            async def confirm(self_, interaction: discord.Interaction, _):
                if interaction.user.id != self_.member.id:
                    return await interaction.response.send_message("not yours", ephemeral=True)
                async with db.pool.acquire() as conn:
                    await conn.execute("DELETE FROM pets WHERE user_id=$1", self_.member.id)
                    await conn.execute("DELETE FROM pet_inventory WHERE user_id=$1", self_.member.id)
                sp_ = SPECIES.get(self_.row_["species"], {})
                await interaction.response.edit_message(
                    content=f"*{sp_.get('emoji','🐾')} {self_.row_['name']} runs off into the distance.*",
                    embed=None, view=None
                )
                self_.stop()

            @discord.ui.button(label="keep", style=discord.ButtonStyle.secondary)
            async def cancel(self_, interaction: discord.Interaction, _):
                await interaction.response.edit_message(content="release cancelled.", embed=None, view=None)
                self_.stop()

        await ctx.send(embed=embed, view=ConfirmRelease(self.bot, ctx.author, row))

    @commands.command(name="pettop", aliases=["petleaderboard", "petlb"], help="top pets by level", usage="!pettop")
    async def pettop(self, ctx):
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT user_id, name, species, level, battles_won FROM pets WHERE is_dead=FALSE ORDER BY level DESC, battles_won DESC LIMIT 10"
            )
        if not rows:
            return await ctx.send("no pets yet.")
        embed = discord.Embed(title="🏆 top pets", color=discord.Color.gold())
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(rows):
            m    = ctx.guild.get_member(r["user_id"])
            owner = m.display_name if m else f"<{r['user_id']}>"
            sp   = SPECIES.get(r["species"], {})
            prefix = medals[i] if i < 3 else f"**{i+1}.**"
            embed.add_field(
                name=f"{prefix} {sp.get('emoji','🐾')} **{r['name']}** (lv.{r['level']})",
                value=f"owner: {owner} | {r['battles_won']}W",
                inline=False
            )
        await ctx.send(embed=embed)

    @tasks.loop(hours=1)
    async def stat_decay_task(self):
        await self.bot.wait_until_ready()
        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, hunger, happiness, health FROM pets WHERE is_dead=FALSE")

            for r in rows:
                new_hunger = max(0, r["hunger"] - 3)
                new_happiness = max(0, r["happiness"] - 2)

                new_health = r["health"]
                if new_hunger == 0:
                    new_health = max(0, new_health - 5)

                await conn.execute(
                    """
                    UPDATE pets
                    SET hunger=$1, happiness=$2, health=$3,
                        xp = xp + 5,
                        skill_xp = skill_xp + 5,
                        is_dead=$4
                    WHERE user_id=$5
                    """,
                    new_hunger,
                    new_happiness,
                    new_health,
                    new_health <= 0,
                    r["user_id"]
                )

    @tasks.loop(hours=24)
    async def age_task(self):
        await self.bot.wait_until_ready()
        async with db.pool.acquire() as conn:
            await conn.execute("UPDATE pets SET age_days=age_days+1 WHERE is_dead=FALSE")


async def setup(bot):
    await bot.add_cog(PetCommands(bot))