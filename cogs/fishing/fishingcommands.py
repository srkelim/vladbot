import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime as dt, timedelta, timezone

from db import db
from config import QUID_EMOJI, SIGWATER_CHANNEL, HEAVEN_CHANNEL, ICY_PEAKS_CHANNEL, MINNEAPOLIS_CHANNEL, HOUSEOFVLADS_CHANNEL, DREAMSKY_CHANNEL, DREAMSKY_ROLE, HEAVEN_ROLE, ICY_PEAKS_ROLE, HELL_LIMBO, HELL_LUST, HELL_GLUTTONY, HELL_GREED, HELL_WRATH, HELL_HERESY, HELL_VIOLENCE, HELL_FRAUD, HELL_TREACHERY
from config import HELL_LIMBO_ROLE, HELL_LUST_ROLE, HELL_GLUTTONY_ROLE, HELL_GREED_ROLE, HELL_WRATH_ROLE, HELL_HERESY_ROLE, HELL_VIOLENCE_ROLE, HELL_FRAUD_ROLE, HELL_TREACHERY_ROLE
from cogs.achievements import hooks

SELL_COOLDOWN_HOURS = 12

HELL_LAYERS = [
    {"name": "limbo", "emoji": "🌫️", "layer_num": 1, "channel": HELL_LIMBO, "role": HELL_LIMBO_ROLE, "tier": "blazing-1", "mechanic": "evil_quid", "boss": None},
    {"name": "lust", "emoji": "❤️‍🔥", "layer_num": 2, "channel": HELL_LUST, "role": HELL_LUST_ROLE, "tier": "blazing-2", "mechanic": None, "boss": "aphrodite"},
    {"name": "gluttony", "emoji": "🍖", "layer_num": 3, "channel": HELL_GLUTTONY, "role": HELL_GLUTTONY_ROLE, "tier": "blazing-3", "mechanic": "fish_discard","boss": None},
    {"name": "greed", "emoji": "🪙", "layer_num": 4, "channel": HELL_GREED, "role": HELL_GREED_ROLE, "tier": "blazing-4", "mechanic": "greed_pool", "boss": None},
    {"name": "wrath", "emoji": "⚡", "layer_num": 5, "channel": HELL_WRATH, "role": HELL_WRATH_ROLE, "tier": "blazing-5", "mechanic": None, "boss": "genghis_khan"},
    {"name": "heresy", "emoji": "🐐", "layer_num": 6, "channel": HELL_HERESY, "role": HELL_HERESY_ROLE, "tier": "blazing-6", "mechanic": None, "boss": "caligula"},
    {"name": "violence", "emoji": "🩸", "layer_num": 7, "channel": HELL_VIOLENCE, "role": HELL_VIOLENCE_ROLE, "tier": "blazing-7", "mechanic": None, "boss": "king_minnea"},
    {"name": "fraud", "emoji": "🎭", "layer_num": 8, "channel": HELL_FRAUD, "role": HELL_FRAUD_ROLE, "tier": "blazing-8", "mechanic": None, "boss": "dealer_sr"},
    {"name": "treachery", "emoji": "🗡️", "layer_num": 9, "channel": HELL_TREACHERY, "role": HELL_TREACHERY_ROLE, "tier": "blazing-9", "mechanic": None, "boss": "anti_vlad"},
]
HELL_CHANNEL_IDS  = {l["channel"] for l in HELL_LAYERS}
HELL_HELLEVATOR_ROLE = 1500910570738683924

def get_hell_layer(channel_id: int) -> dict | None:
    for layer in HELL_LAYERS:
        if layer["channel"] == channel_id:
            return layer
    return None

def get_hell_layer_by_name(name: str) -> dict | None:
    for layer in HELL_LAYERS:
        if layer["name"] == name.lower():
            return layer
    return None

RODS = {
    "stick": {
        "name": "stick",
        "emoji": "🪵",
        "price": 50,
        "description": "a literal stick",
        "weights": {
            "junk": 70,
            "common": 25,
            "uncommon": 4,
            "rare": 1,
            "legendary": 0,
        },
    },
    "wooden_rod": {
        "name": "wooden rod",
        "emoji": "🎣",
        "price": 200,
        "description": "a basic fishing rod",
        "weights": {
            "junk": 45,
            "common": 40,
            "uncommon": 12,
            "rare": 3,
            "legendary": 0,
        },
    },
    "iron_rod": {
        "name": "iron rod",
        "emoji": "⚙️",
        "price": 600,
        "description": "sturdy and reliable rod",
        "weights": {
            "junk": 25,
            "common": 40,
            "uncommon": 25,
            "rare": 9,
            "legendary": 1,
        },
    },
    "crystal_rod": {
        "name": "crystal rod",
        "emoji": "💎",
        "price": 1500,
        "description": "glimmers in the water",
        "weights": {
            "junk": 10,
            "common": 25,
            "uncommon": 35,
            "rare": 25,
            "legendary": 5,
            "vacation-sigwater": 2, "vacation-minneapolis": 2, "vacation-dreamsky": 2, "vacation-heaven": 2, "vacation-icypeaks": 2, "vacation-houseofvlads": 2
        },
    },
    "dragon_rod": {
        "name": "dragon rod",
        "emoji": "🐉",
        "price": 5000,
        "description": "forged from dragon bone",
        "weights": {
            "junk": 5,
            "common": 15,
            "uncommon": 30,
            "rare": 35,
            "legendary": 15,
            "abyssal": 0,
            "vacation-sigwater": 2, "vacation-minneapolis": 2, "vacation-dreamsky": 2, "vacation-heaven": 2, "vacation-icypeaks": 2, "vacation-houseofvlads": 2
        },
    },
    "sigshark_rod": {
        "name": "sharkfang rod",
        "emoji": "🦷",
        "price": 0,
        "description": "carved from the teeth of the supreme sigshark",
        "weights": {
            "junk": 3,
            "common": 8,
            "uncommon": 20,
            "rare": 30,
            "legendary": 37,
            "abyssal": 2,
            "vacation-sigwater": 2, "vacation-minneapolis": 2, "vacation-dreamsky": 2, "vacation-heaven": 2, "vacation-icypeaks": 2, "vacation-houseofvlads": 2
        },
    },
    "dreamsky_trident": {
        "name": "dreamsky trident",
        "emoji": "🔱",
        "price": 0,
        "description": "forged from every rod and a philosopher's soul",
        "weights": {"junk": 2, "common": 8, "uncommon": 20, "rare": 30, "legendary": 35, "abyssal": 5, "vacation-sigwater": 2, "vacation-minneapolis": 2, "vacation-dreamsky": 2, "vacation-heaven": 2, "vacation-icypeaks": 2, "vacation-houseofvlads": 2},
        "multi_catch": 5,
    },
    "pitchfork": {
        "name": "pitchfork",
        "emoji": "🔱",
        "price": 0,
        "description": "forged in hell",
        "weights": {
            "junk": 2, "common": 5, "uncommon": 10, "rare": 18, "legendary": 25, "abyssal": 15,
            "blazing-1": 5, "blazing-2": 5, "blazing-3": 5, "blazing-4": 5, "blazing-5": 5,
            "blazing-6": 5, "blazing-7": 5, "blazing-8": 5, "blazing-9": 1,
            "vacation-sigwater": 2, "vacation-minneapolis": 2, "vacation-dreamsky": 2, "vacation-heaven": 2, "vacation-icypeaks": 2, "vacation-houseofvlads": 2
        },
        "multi_catch": 3,
    },
}

SHOP_RODS = {k: v for k, v in RODS.items() if k not in ("sigshark_rod", "dreamsky_trident", "pitchfork")}

BAIT_ITEMS = {
    "common_bait": {
        "name": "common bait",
        "emoji": "🪱",
        "price": 25,
        "description": "boosts common fish chance on your next cast",
        "column": "common_bait",
        "modifier": {"common": 3.0},
    },
    "rare_bait": {
        "name": "rare bait",
        "emoji": "💠",
        "price": 150,
        "description": "boosts rare fish chance on your next cast",
        "column": "rare_bait",
        "modifier": {"rare": 3.0, "junk": 0.3, "common": 0.5},
    },
    "legendary_bait": {
        "name": "legendary bait",
        "emoji": "✨",
        "price": 300,
        "description": "greatly boosts legendary fish chance on your next cast",
        "column": "legendary_bait",
        "modifier": {"legendary": 4.0, "junk": 0.2, "common": 0.3, "uncommon": 0.7},
    },
    "deep_bait": {
        "name": "deep bait",
        "emoji": "🌑",
        "price": 500,
        "description": "grants a higher chance of catching abyssal loot.\ndoesn't work if equipped rod can't catch abyssal loot",
        "column": "deep_bait",
        "modifier": {"abyssal": 1.5, "legendary": 2.0, "junk": 0.2},
    },
}

CAPACITY_TIERS = [
    (50,  0),
    (100, 5_000),
    (200, 25_000),
    (500, 75_000),
    (None, 2_500_000),
]

CHANNEL_MODIFIERS = {
    SIGWATER_CHANNEL: {
        "junk": 2.5, "common": 0.8, "uncommon": 0.4, "rare": 0.2, "legendary": 0.1,
        "vacation-sigwater": 6.0, "label": "sigwater", "emoji": "💀",
    },
    HEAVEN_CHANNEL: {
        "junk": 0.1, "common": 0.6, "uncommon": 1.2, "rare": 2.0, "legendary": 2.0,
        "vacation-heaven": 6.0, "label": "heaven", "emoji": "🕊️",
    },
    ICY_PEAKS_CHANNEL: {
        "junk": 0.5, "common": 0.9, "uncommon": 1.5, "rare": 1.8, "legendary": 1.2,
        "vacation-icypeaks": 6.0, "label": "icy peaks", "emoji": "❄️",
    },
    MINNEAPOLIS_CHANNEL: {
        "junk": 0.8, "common": 1.0, "uncommon": 1.4, "rare": 1.1, "legendary": 1.0,
        "vacation-minneapolis": 6.0, "label": "minneapolis", "emoji": "🏙️",
    },
    HOUSEOFVLADS_CHANNEL: {
        "junk": 0.6, "common": 0.9, "uncommon": 1.2, "rare": 1.4, "legendary": 1.1,
        "vacation-houseofvlads": 6.0, "label": "house of vlads", "emoji": "💀",
    },
    DREAMSKY_CHANNEL: {
        "junk": 0.1, "common": 0.3, "uncommon": 0.8, "rare": 1.5, "legendary": 2.5,
        "vacation-dreamsky": 6.0, "label": "dream sky", "emoji": "✨",
    },
    HELL_LIMBO: {
        "junk": 0.5, "common": 0.6, "uncommon": 0.8, "rare": 1.0, "legendary": 1.2,
        "abyssal": 1.5, "blazing-1": 8.0, "label": "limbo", "emoji": "🌫️",
    },
    HELL_LUST: {
        "junk": 0.4, "common": 0.5, "uncommon": 0.7, "rare": 0.9, "legendary": 1.1,
        "abyssal": 1.4, "blazing-1": 2.0, "blazing-2": 8.0, "label": "lust", "emoji": "❤️‍🔥",
    },
    HELL_GLUTTONY: {
        "junk": 0.3, "common": 0.4, "uncommon": 0.6, "rare": 0.8, "legendary": 1.0,
        "abyssal": 1.3, "blazing-2": 2.0, "blazing-3": 8.0, "label": "gluttony", "emoji": "🍖",
    },
    HELL_GREED: {
        "junk": 0.3, "common": 0.3, "uncommon": 0.5, "rare": 0.7, "legendary": 0.9,
        "abyssal": 1.2, "blazing-3": 2.0, "blazing-4": 8.0, "label": "greed", "emoji": "🪙",
    },
    HELL_WRATH: {
        "junk": 0.2, "common": 0.3, "uncommon": 0.4, "rare": 0.6, "legendary": 0.8,
        "abyssal": 1.1, "blazing-4": 2.0, "blazing-5": 8.0, "label": "wrath", "emoji": "⚡",
    },
    HELL_HERESY: {
        "junk": 0.2, "common": 0.2, "uncommon": 0.3, "rare": 0.5, "legendary": 0.7,
        "abyssal": 1.0, "blazing-5": 2.0, "blazing-6": 8.0, "label": "heresy", "emoji": "🐐",
    },
    HELL_VIOLENCE: {
        "junk": 0.1, "common": 0.2, "uncommon": 0.3, "rare": 0.4, "legendary": 0.6,
        "abyssal": 0.9, "blazing-6": 2.0, "blazing-7": 8.0, "label": "violence", "emoji": "🩸",
    },
    HELL_FRAUD: {
        "junk": 0.1, "common": 0.1, "uncommon": 0.2, "rare": 0.3, "legendary": 0.5,
        "abyssal": 0.8, "blazing-7": 2.0, "blazing-8": 8.0, "label": "fraud", "emoji": "🎭",
    },
    HELL_TREACHERY: {
        "junk": 0.1, "common": 0.1, "uncommon": 0.2, "rare": 0.3, "legendary": 0.4,
        "abyssal": 0.7, "blazing-8": 2.0, "blazing-9": 8.0, "label": "treachery", "emoji": "🗡️",
    },
}

FISH = {
    "old_boot":      {"name": "old boot",      "emoji": "👢", "tier": "junk",      "value": 1},
    "seaweed":       {"name": "seaweed",        "emoji": "🌿", "tier": "junk",      "value": 1},
    "tin_can":       {"name": "tin can",        "emoji": "🥫", "tier": "junk",      "value": 1},
    "soggy_paper":   {"name": "soggy paper",    "emoji": "📄", "tier": "junk",      "value": 1},

    "sardine":       {"name": "sardine",        "emoji": "🐟", "tier": "common",    "value": 10},
    "carp":          {"name": "carp",           "emoji": "🐠", "tier": "common",    "value": 12},
    "trout":         {"name": "trout",          "emoji": "🐡", "tier": "common",    "value": 15},
    "catfish":       {"name": "catfish",        "emoji": "😺", "tier": "common",    "value": 14},

    "bass":          {"name": "bass",           "emoji": "🎸", "tier": "uncommon",  "value": 25},
    "pike":          {"name": "pike",           "emoji": "⚔️",  "tier": "uncommon",  "value": 30},
    "salmon":        {"name": "salmon",         "emoji": "🍣",  "tier": "uncommon",  "value": 20},
    "eel":           {"name": "eel",            "emoji": "🐍", "tier": "uncommon",  "value": 25},

    "swordfish":     {"name": "swordfish",      "emoji": "🗡️",  "tier": "rare",      "value": 39},
    "shark":         {"name": "shark",          "emoji": "🦈", "tier": "rare",      "value": 37},
    "octopus":       {"name": "octopus",        "emoji": "🐙", "tier": "rare",      "value": 31},
    "golden_carp":   {"name": "golden carp",    "emoji": "✨", "tier": "rare",      "value": 35},

    "sea_dragon":    {"name": "sea dragon",     "emoji": "🐲", "tier": "legendary", "value": 45},
    "kraken_arm":    {"name": "kraken arm",     "emoji": "🦑", "tier": "legendary", "value": 50},
    "ancient_fish":  {"name": "ancient fish",   "emoji": "🏺", "tier": "legendary", "value": 65},
    "ghost_whale":   {"name": "ghost whale",    "emoji": "🐳", "tier": "legendary", "value": 40},

    "void_angler":     {"name": "void angler",    "emoji": "🕳️", "tier": "abyssal", "value": 70},
    "abyss_leviathan": {"name": "abyss leviathan","emoji": "🌑", "tier": "abyssal", "value": 70},
    "the_deep_one":    {"name": "dreadful shrimp of eternal undeniable regret and despair", "emoji": "🦐", "tier": "abyssal", "value": 70},
    "sigshark_fang":   {"name": "dealer's hat",   "emoji": "🎩", "tier": "abyssal", "value": 70},

    "sludge_eel":      {"name": "sludge eel",       "emoji": "🤢", "tier": "vacation-sigwater",    "value": 25},
    "bile_carp":       {"name": "bile carp",         "emoji": "🟢", "tier": "vacation-sigwater",    "value": 30},
    "rust_shark":      {"name": "rust shark",        "emoji": "🪝", "tier": "vacation-sigwater",    "value": 20},
    "memory_fish":     {"name": "memory fish",       "emoji": "💧", "tier": "vacation-sigwater",    "value": 40},

    "city_catfish":    {"name": "city catfish",      "emoji": "🏙️", "tier": "vacation-minneapolis", "value": 25},
    "storm_drain_eel": {"name": "storm drain eel",   "emoji": "🌧️", "tier": "vacation-minneapolis", "value": 35},
    "concrete_bass":   {"name": "concrete bass",     "emoji": "🧱", "tier": "vacation-minneapolis", "value": 20},
    "tax_trout":       {"name": "tax trout",         "emoji": "💸", "tier": "vacation-minneapolis", "value": 40},

    "cloud_drifter":   {"name": "cloud drifter",     "emoji": "☁️", "tier": "vacation-heaven",      "value": 25},
    "halo_ray":        {"name": "halo ray",           "emoji": "👼", "tier": "vacation-heaven",      "value": 30},
    "saint_salmon":    {"name": "saint salmon",      "emoji": "✝️", "tier": "vacation-heaven",      "value": 20},
    "forgiven_pike":   {"name": "forgiven pike",     "emoji": "🕊️", "tier": "vacation-heaven",      "value": 40},

    "bone_carp":       {"name": "bone carp",         "emoji": "🦴", "tier": "vacation-houseofvlads","value": 25},
    "marrow_eel":      {"name": "marrow eel",        "emoji": "⬜", "tier": "vacation-houseofvlads","value": 30},
    "crypt_bass":      {"name": "crypt bass",        "emoji": "💀", "tier": "vacation-houseofvlads","value": 20},
    "ribs_of_vlad":    {"name": "ribs of vlad",      "emoji": "🩻", "tier": "vacation-houseofvlads","value": 40},

    "frost_pike":      {"name": "frost pike",        "emoji": "🧊", "tier": "vacation-icypeaks",    "value": 25},
    "glacier_eel":     {"name": "glacier eel",       "emoji": "🏔️", "tier": "vacation-icypeaks",    "value": 30},
    "snowblind_carp":  {"name": "snowblind carp",    "emoji": "🌨️", "tier": "vacation-icypeaks",    "value": 20},
    "yeti_minnow":     {"name": "yeti minnow",       "emoji": "🦣", "tier": "vacation-icypeaks",    "value": 40},

    "starlight_ray":   {"name": "starlight ray",     "emoji": "⭐", "tier": "vacation-dreamsky",    "value": 25},
    "cloud_serpent":   {"name": "cloud serpent",     "emoji": "🌤️", "tier": "vacation-dreamsky",    "value": 30},
    "prism_whale":     {"name": "prism whale",       "emoji": "🌈", "tier": "vacation-dreamsky",    "value": 20},
    "ethels_gaze":     {"name": "ethel's gaze",      "emoji": "👁️", "tier": "vacation-dreamsky",    "value": 40},

    "pale_wanderer":   {"name": "pale wanderer",     "emoji": "🌫️", "tier": "blazing-1", "value": 80},
    "grey_drift":      {"name": "grey drift",         "emoji": "🩶", "tier": "blazing-1", "value": 80},
    "lost_soul_fish":  {"name": "lost soul fish",    "emoji": "👻", "tier": "blazing-1", "value": 80},
    "sighing_ray":     {"name": "sighing ray",        "emoji": "💨", "tier": "blazing-1", "value": 80},

    "velvet_eel":      {"name": "velvet eel",         "emoji": "🩷", "tier": "blazing-2", "value": 82},
    "passion_pike":    {"name": "passion pike",       "emoji": "💋", "tier": "blazing-2", "value": 82},
    "burning_manta":   {"name": "burning manta",      "emoji": "❤️‍🔥","tier": "blazing-2", "value": 82},
    "crimson_dart":    {"name": "crimson dart",       "emoji": "🎯", "tier": "blazing-2", "value": 82},

    "gorge_carp":      {"name": "gorge carp",         "emoji": "🍖", "tier": "blazing-3", "value": 84},
    "bottomless_eel":  {"name": "bottomless eel",     "emoji": "🕳️", "tier": "blazing-3", "value": 84},
    "feast_shark":     {"name": "feast shark",        "emoji": "🍽️", "tier": "blazing-3", "value": 84},
    "bloat_whale":     {"name": "bloat whale",        "emoji": "🐋", "tier": "blazing-3", "value": 84},

    "coin_carp":       {"name": "coin carp",          "emoji": "🪙", "tier": "blazing-4", "value": 86},
    "greed_lamprey":   {"name": "greed lamprey",      "emoji": "💰", "tier": "blazing-4", "value": 86},
    "hoard_leviathan": {"name": "hoard leviathan",    "emoji": "💎", "tier": "blazing-4", "value": 86},
    "gold_gulper":     {"name": "gold gulper",        "emoji": "🏆", "tier": "blazing-4", "value": 86},

    "rage_barracuda":  {"name": "rage barracuda",     "emoji": "⚡", "tier": "blazing-5", "value": 88},
    "fury_shark":      {"name": "fury shark",         "emoji": "🔴", "tier": "blazing-5", "value": 88},
    "smoldering_pike": {"name": "smoldering pike",    "emoji": "🔥", "tier": "blazing-5", "value": 88},
    "wrath_serpent":   {"name": "wrath serpent",      "emoji": "🐉", "tier": "blazing-5", "value": 88},

    "inverted_angel":  {"name": "inverted angel",     "emoji": "🙃", "tier": "blazing-6", "value": 90},
    "false_prophet":   {"name": "false prophet",      "emoji": "🐐", "tier": "blazing-6", "value": 95},
    "hollow_saint":    {"name": "hollow saint",       "emoji": "💀", "tier": "blazing-6", "value": 90},
    "broken_halo_eel": {"name": "broken halo eel",    "emoji": "😈", "tier": "blazing-6", "value": 90},

    "bone_crusher":    {"name": "bone crusher",       "emoji": "🦴", "tier": "blazing-7", "value": 93},
    "blood_tide_ray":  {"name": "blood tide ray",     "emoji": "🩸", "tier": "blazing-7", "value": 93},
    "war_whale":       {"name": "war whale",          "emoji": "⚔️", "tier": "blazing-7", "value": 93},
    "siege_leviathan": {"name": "siege leviathan",    "emoji": "🏴", "tier": "blazing-7", "value": 93},

    "liar_fish":       {"name": "liar fish",           "emoji": "🎭", "tier": "blazing-8", "value": 96},
    "deceiver_ray":    {"name": "deceiver ray",        "emoji": "🃏", "tier": "blazing-8", "value": 96},
    "false_trident":   {"name": "false trident",       "emoji": "🔱", "tier": "blazing-8", "value": 96},
    "the_accountant":  {"name": "the accountant",      "emoji": "📋", "tier": "blazing-8", "value": 96},

    "turncoat_eel":    {"name": "turncoat eel",        "emoji": "🗡️", "tier": "blazing-9", "value": 97},
    "void_betrayer":   {"name": "void betrayer",       "emoji": "🕳️", "tier": "blazing-9", "value": 98},
    "knife_ray":       {"name": "knife ray",           "emoji": "🔪", "tier": "blazing-9", "value": 99},
    "the_last_vlad":   {"name": "the last vlad",       "emoji": "💀", "tier": "blazing-9", "value": 100},
}

FISH_BY_TIER: dict[str, list[str]] = {}
for fish_id, fish in FISH.items():
    FISH_BY_TIER.setdefault(fish["tier"], []).append(fish_id)

TIER_ORDER = [
    "junk", "common", "uncommon", "rare", "legendary", "abyssal",
    "vacation-sigwater", "vacation-minneapolis", "vacation-heaven",
    "vacation-houseofvlads", "vacation-icypeaks", "vacation-dreamsky",
    "blazing-1", "blazing-2", "blazing-3", "blazing-4", "blazing-5",
    "blazing-6", "blazing-7", "blazing-8", "blazing-9",
]

VACATION_TIERS = {
    SIGWATER_CHANNEL:"vacation-sigwater",
    MINNEAPOLIS_CHANNEL:"vacation-minneapolis",
    HEAVEN_CHANNEL:"vacation-heaven",
    HOUSEOFVLADS_CHANNEL:"vacation-houseofvlads",
    ICY_PEAKS_CHANNEL:"vacation-icypeaks",
    DREAMSKY_CHANNEL:"vacation-dreamsky",
}

TIER_COLORS = {
    "junk": discord.Color.from_rgb(120, 120, 120),
    "common": discord.Color.green(),
    "uncommon": discord.Color.blue(),
    "rare": discord.Color.purple(),
    "legendary": discord.Color.gold(),
    "abyssal": discord.Color.from_rgb(10, 0, 20),
    "vacation-sigwater": discord.Color.from_rgb(40, 80, 40),
    "vacation-minneapolis": discord.Color.from_rgb(60, 60, 90),
    "vacation-heaven": discord.Color.from_rgb(230, 220, 180),
    "vacation-houseofvlads": discord.Color.from_rgb(80, 60, 40),
    "vacation-icypeaks": discord.Color.from_rgb(180, 220, 255),
    "vacation-dreamsky": discord.Color.from_rgb(180, 160, 255),
    "blazing-1": discord.Color.from_rgb(160, 150, 140),
    "blazing-2": discord.Color.from_rgb(220, 80, 120),
    "blazing-3": discord.Color.from_rgb(180, 100, 40),
    "blazing-4": discord.Color.from_rgb(220, 180, 0),
    "blazing-5": discord.Color.from_rgb(230, 50, 0),
    "blazing-6": discord.Color.from_rgb(100, 0, 180),
    "blazing-7": discord.Color.from_rgb(160, 0, 0),
    "blazing-8": discord.Color.from_rgb(20, 20, 20),
    "blazing-9": discord.Color.from_rgb(0, 0, 0),
}

SIGSHARK_CHANCE   = 0.05
SIGSHARK_REWARD   = 1500
SIGSHARK_COOLDOWN = 24

DODGE_ATTACKS = {
    "🦈 LUNGE LEFT":  "right",
    "🦈 LUNGE RIGHT": "left",
    "🦈 TAIL SLAM":   "dive",
    "🦈 DEEP BITE":   "jump",
}
DODGE_TIME = 7

REEL_ROUNDS  = 5
REEL_NEEDED  = 5
REEL_WIND_UP = (2.5, 5.0)
REEL_WINDOW  = 1.5

BAIT_FISH        = ["🐟", "🦈", "🐡", "🐙", "🐠", "🦑", "🐬", "🦐"]
BAIT_SEQ_LEN     = 8
BAIT_SPEED       = 1.0
BAIT_QUESTIONS   = 3
BAIT_NEEDED      = 2
BAIT_ANSWER_TIME = 10

def apply_channel_modifier(base_weights: dict, channel_id: int) -> dict:
    modifier = CHANNEL_MODIFIERS.get(channel_id)
    if not modifier:
        return base_weights
    return {
        tier: base_weights[tier] * modifier.get(tier, 1.0)
        for tier in base_weights
    }


def pick_catch(rod_id: str, channel_id: int, bait_modifier: dict | None = None) -> str:
    rod = RODS[rod_id]
    weights = dict(apply_channel_modifier(rod["weights"], channel_id))

    abyssal_capable = ("sigshark_rod", "dreamsky_trident", "pitchfork")
    if rod_id not in abyssal_capable:
        weights.pop("abyssal", None)

    if rod_id == "pitchfork":
        layer = get_hell_layer(channel_id)
        for tier in list(weights):
            if tier.startswith("blazing") and (not layer or tier != layer["tier"]):
                weights.pop(tier, None)
    else:
        for tier in list(weights):
            if tier.startswith("blazing"):
                weights.pop(tier, None)

    vac_tier = VACATION_TIERS.get(channel_id)
    for tier in list(weights):
        if tier.startswith("vacation") and tier != vac_tier:
            weights.pop(tier, None)

    if bait_modifier:
        for tier, mult in bait_modifier.items():
            if tier in weights:
                weights[tier] *= mult

    tiers = [t for t, w in weights.items() if w > 0 and t in FISH_BY_TIER]
    tier_weights = [weights[t] for t in tiers]
    chosen_tier = random.choices(tiers, weights=tier_weights, k=1)[0]
    return random.choice(FISH_BY_TIER[chosen_tier])


async def get_equipped_rod(user_id: int) -> str | None:
    async with db.pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT rod_id FROM user_rods WHERE user_id = $1",
            user_id,
        )


async def set_equipped_rod(user_id: int, rod_id: str):
    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_rods (user_id, rod_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET rod_id = $2
            """,
            user_id, rod_id,
        )


async def add_fish(user_id: int, fish_id: str) -> bool:
    """Add a fish. Returns False if bag is full."""
    capacity = await get_fish_capacity(user_id)
    if capacity is not None:
        current = await get_fish_count(user_id)
        if current >= capacity:
            return False
    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO fish_inventory (user_id, fish_id, quantity)
            VALUES ($1, $2, 1)
            ON CONFLICT (user_id, fish_id) DO UPDATE
                SET quantity = fish_inventory.quantity + 1
            """,
            user_id, fish_id,
        )
    return True

async def get_active_bait(user_id: int) -> str | None:
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT common_bait, rare_bait, legendary_bait, deep_bait FROM user_bait WHERE user_id = $1",
            user_id
        )
    if not row:
        return None
    for col in ("common_bait", "rare_bait", "legendary_bait", "deep_bait"):
        if row[col] > 0:
            return col
    return None


async def get_fish_capacity(user_id: int) -> int | None:
    """Returns capacity (None = unlimited)."""
    async with db.pool.acquire() as conn:
        level = await conn.fetchval(
            "SELECT fish_bag_upgrade FROM user_unlocks WHERE user_id = $1",
            user_id
        ) or 0
    slots, _ = CAPACITY_TIERS[min(level, len(CAPACITY_TIERS) - 1)]
    return slots


async def get_fish_count(user_id: int) -> int:
    async with db.pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT COALESCE(SUM(quantity), 0) FROM fish_inventory WHERE user_id = $1",
            user_id
        )
    return total or 0


async def consume_bait(user_id: int, column: str):
    async with db.pool.acquire() as conn:
        await conn.execute(
            f"UPDATE user_bait SET {column} = {column} - 1 WHERE user_id = $1",
            user_id
        )


async def add_bait(user_id: int, column: str, amount: int = 1):
    async with db.pool.acquire() as conn:
        await conn.execute(
            f"""
            INSERT INTO user_bait (user_id, {column})
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET {column} = COALESCE(user_bait.{column}, 0) + $2
            """,
            user_id, amount
        )

async def record_catch(user_id: int, fish_id: str) -> bool:
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            """
            INSERT INTO fish_caught (user_id, fish_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id, fish_id) DO NOTHING
            """,
            user_id, fish_id
        )
    return result == "INSERT 0 1"


async def get_caught_set(user_id: int) -> set:
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT fish_id FROM fish_caught WHERE user_id = $1", user_id
        )
    return {r["fish_id"] for r in rows}

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

class SigsharKView(discord.ui.View):
    def __init__(self, bot, challenger):
        super().__init__(timeout=60)
        self.bot = bot
        self.challenger = challenger

    @discord.ui.button(label="fight the sigshark", style=discord.ButtonStyle.danger, emoji="🦈")
    async def fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        channel = interaction.channel

        if member.id != self.challenger.id:
            return await interaction.response.send_message(
                "this isn't your fight.",
                ephemeral=True
            )

        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT last_fight FROM enemy_cooldowns WHERE user_id=$1 AND enemy=$2",
                member.id, "supreme_sigshark"
            )

        if row:
            cooldown_end = row["last_fight"] + timedelta(hours=SIGSHARK_COOLDOWN)
            if cooldown_end > dt.now(timezone.utc):
                ts = int(cooldown_end.timestamp())
                return await interaction.response.send_message(
                    f"🦈 the sigshark remembers you. it won't surface again until <t:{ts}:R>.",
                    ephemeral=True
                )

        self.stop()

        await interaction.response.send_message(
            embed=discord.Embed(
                description="🦈 **you enter the water...**\n*the sigshark stirs in the deep.*",
                color=discord.Color.from_rgb(30, 10, 40),
            ),
            ephemeral=True
        )


        try:
            await channel.send(embed=discord.Embed(
                title="🦈 SUPREME SIGSHARK",
                description=(
                    f"**{member.mention}** has challenged the **Supreme Sigshark**!\n\n"
                    "3 phases. fail any one and you lose.\n\n"
                    "*the water darkens...*"
                ),
                color=discord.Color.from_rgb(20, 5, 30),
            ))
            await asyncio.sleep(3)

            await channel.send(embed=discord.Embed(
                description="\n**phase 1 of 3** - dodge\n",
                color=discord.Color.from_rgb(30, 10, 40),
            ))

            if not await phase_dodge(self.bot, channel, member):
                await channel.send(embed=discord.Embed(
                    title="💀 DEFEATED",
                    description=f"**{member.mention}** was destroyed in phase 1.\nthe sigshark returns to the deep.",
                    color=discord.Color.dark_red(),
                ))
                return

            await channel.send(embed=discord.Embed(
                description="✅ **phase 1 cleared.** the shark is wounded but not done.",
                color=discord.Color.green(),
            ))
            await asyncio.sleep(2)

            await channel.send(embed=discord.Embed(
                description="\n**phase 2 of 3** - reel\n",
                color=discord.Color.from_rgb(30, 10, 40),
            ))

            if not await phase_reel(self.bot, channel, member):
                await channel.send(embed=discord.Embed(
                    title="💀 DEFEATED",
                    description=f"**{member.mention}** lost the line in phase 2.\nthe sigshark escapes.",
                    color=discord.Color.dark_red(),
                ))
                return

            await channel.send(embed=discord.Embed(
                description="✅ **phase 2 cleared.** it's almost over. land the final blow.",
                color=discord.Color.green(),
            ))
            await asyncio.sleep(2)

            await channel.send(embed=discord.Embed(
                description="\n**phase 3 of 3** - strike\n",
                color=discord.Color.from_rgb(30, 10, 40),
            ))

            if not await phase_strike(self.bot, channel, member):
                await channel.send(embed=discord.Embed(
                    title="💀 DEFEATED",
                    description=f"**{member.mention}** crumbled at the final phase.\nso close.",
                    color=discord.Color.dark_red(),
                ))
                return

            rod_dropped = True

            async with db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO economy (user_id, quid)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) DO UPDATE SET quid = economy.quid + $2
                    """,
                    member.id, SIGSHARK_REWARD,
                )
                await conn.execute(
                    """
                    INSERT INTO enemy_cooldowns (user_id, enemy, last_fight)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id, enemy)
                    DO UPDATE SET last_fight = EXCLUDED.last_fight
                    """,
                    member.id, "supreme_sigshark", dt.now(timezone.utc)
                )

                already_has_rod = await conn.fetchval(
                    "SELECT sigshark_rod FROM user_unlocks WHERE user_id = $1",
                    member.id
                )

                if rod_dropped and not already_has_rod:
                    await conn.execute(
                        """
                        INSERT INTO user_unlocks (user_id, sigshark_rod)
                        VALUES ($1, TRUE)
                        ON CONFLICT (user_id) DO UPDATE SET sigshark_rod = TRUE
                        """,
                        member.id
                    )
                    await set_equipped_rod(member.id, "sigshark_rod")

            await hooks.on_sigshark_defeat(self.bot, member)

            rod_line = (
                "\n🦷 **the sharkfang rod dropped!** it has been equipped."
                if rod_dropped and not already_has_rod
                else (
                    "\n🦷 *the sharkfang rod dropped but you already have one.*"
                    if rod_dropped and already_has_rod
                    else ""
                )
            )

            await channel.send(embed=discord.Embed(
                title="🏆 SUPREME SIGSHARK DEFEATED",
                description=(
                    f"**{member.mention}** conquered the deep!\n\n"
                    f"💰 reward: **{SIGSHARK_REWARD} {QUID_EMOJI}**"
                    f"{rod_line}\n\n"
                    "*sigwater is calm again... for now.*"
                ),
                color=discord.Color.gold(),
            ))

        finally:
            self.bot._fishing_users.discard(member.id)

class RodShopButton(discord.ui.Button):
    def __init__(self, rod_id: str, rod: dict):
        super().__init__(
            label=rod["name"],
            style=discord.ButtonStyle.primary,
            custom_id=f"shop_buy_rod_{rod_id}",
        )
        self.rod_id = rod_id
        self.rod = rod

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        rod = self.rod

        async with db.pool.acquire() as conn:
            already_owned = await conn.fetchval(
                "SELECT 1 FROM user_owned_rods WHERE user_id = $1 AND rod_id = $2",
                member.id, self.rod_id
            )
            if already_owned:
                return await interaction.response.send_message(
                    "❌ you already own this rod", ephemeral=True
                )

            quid = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1", member.id
            ) or 0

            if quid < rod["price"]:
                return await interaction.response.send_message(
                    "❌ you don't have enough quid", ephemeral=True
                )

            await conn.execute(
                "UPDATE economy SET quid = quid - $1 WHERE user_id = $2",
                rod["price"], member.id,
            )
            await conn.execute(
                "INSERT INTO user_owned_rods (user_id, rod_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                member.id, self.rod_id
            )

        await set_equipped_rod(member.id, self.rod_id)

        await interaction.response.send_message(
            f"✅ bought and equipped **{rod['emoji']} {rod['name']}** for {rod['price']} {QUID_EMOJI}",
            ephemeral=True,
        )

class FishingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="fish", help="go fishing", usage="!fish")
    async def fish(self, ctx):
        self.bot._fishing_users = getattr(self.bot, "_fishing_users", set())
        self.bot._fishing_users.add(ctx.author.id)
        rod_id = await get_equipped_rod(ctx.author.id)

        if not rod_id:
            return await ctx.send("you don't have a rod! buy one from `!shop`")

        rod = RODS[rod_id]
        channel_id = ctx.channel.id

        if channel_id == SIGWATER_CHANNEL and random.random() < SIGSHARK_CHANCE:
            embed = discord.Embed(
                title="🦈 SOMETHING STIRS",
                description=(
                    "*sigwater goes completely still.*\n"
                    "**the Supreme Sigshark has surfaced.**\n\n"
                    "do you dare fight it?"
                ),
                color=discord.Color.from_rgb(20, 5, 30),
            )
            return await ctx.send(embed=embed, view=SigsharKView(self.bot, ctx.author))

        try:
            bait_col = await get_active_bait(ctx.author.id)
            bait_modifier = None
            bait_line = ""
            if bait_col:
                bait_item = next(b for b in BAIT_ITEMS.values() if b["column"] == bait_col)
                if bait_col == "deep_bait" and channel_id != SIGWATER_CHANNEL:
                    bait_line = f"*(deep bait has no effect outside sigwater)*\n"
                else:
                    bait_modifier = bait_item["modifier"]
                    bait_line = f"bait: {bait_item['emoji']} **{bait_item['name']}** active\n"
                await consume_bait(ctx.author.id, bait_col)

            multi = rod.get("multi_catch", 1)
            channel_mod = CHANNEL_MODIFIERS.get(channel_id)
            location_line = (
                f"location: {channel_mod['emoji']} **{channel_mod['label']}**\n"
                if channel_mod else ""
            )

            capacity = await get_fish_capacity(ctx.author.id)
            current_count = await get_fish_count(ctx.author.id)
            multi = rod.get("multi_catch", 1)
            slots_left = (capacity - current_count) if capacity is not None else multi

            if slots_left <= 0:
                await ctx.send(
                    f"🎒 your fish bag is full! `!sell` your fish or upgrade capacity with `!bagupgrade`."
                )
            elif multi == 1:
                fish_id = pick_catch(rod_id, channel_id, bait_modifier)
                fish = FISH[fish_id]
                added = await add_fish(ctx.author.id, fish_id)
                if not added:
                    return await ctx.send("🎒 your fish bag is full! `!sell` your fish or use `!bagupgrade`.")
                first_catch = await record_catch(ctx.author.id, fish_id)
                tier_label = fish["tier"]
                new_catch_line = "📖 **new fishbook entry!**\n" if first_catch else ""

                embed = discord.Embed(
                    title=f"{fish['emoji']} you caught a **{fish['name']}**!",
                    description=(
                        f"{location_line}"
                        f"{bait_line}"
                        f"{new_catch_line}"
                        f"tier: **{tier_label}**\n"
                        f"sell value: **{fish['value']} quid**\n\n"
                        f"rod used: {rod['emoji']} {rod['name']}"
                    ),
                    color=TIER_COLORS[tier_label],
                )
                if tier_label == "legendary":
                    embed.set_footer(text="🌟 LEGENDARY catch!!")
                elif tier_label == "abyssal":
                    embed.set_footer(text="🕳️ ABYSSAL catch... something ancient surfaces.")
                elif tier_label.startswith("blazing"):
                    num = tier_label.split("-")[1]
                    layer = get_hell_layer(channel_id)
                    ln = layer["name"] if layer else f"tier {num}"
                    embed.set_footer(text=f"🔥 BLAZING tier {num} catch {ln}!!")
                elif tier_label.startswith("vacation"):
                    embed.set_footer(text=f"🌍 location exclusive catch")

                await ctx.send(embed=embed)

                if tier_label == "abyssal":
                    await hooks.on_abyssal_catch(self.bot, ctx.author)
                if tier_label.startswith("blazing"):
                    await hooks.on_blazing_catch(self.bot, ctx.author, tier_label)
                if first_catch:
                    await hooks.on_fishbook_entry(self.bot, ctx.author)

                if channel_id in HELL_CHANNEL_IDS:
                    evil = FISH[fish_id]["value"] // 5
                    if evil > 0:
                        async with db.pool.acquire() as conn:
                            await conn.execute(
                                """
                                INSERT INTO evil_quid (user_id, amount)
                                VALUES ($1, $2)
                                ON CONFLICT (user_id) DO UPDATE SET amount = evil_quid.amount + $2
                                """,
                                ctx.author.id, evil
                            )

            else:
                actual_multi = min(multi, slots_left)
                catches = [pick_catch(rod_id, channel_id, bait_modifier) for _ in range(actual_multi)]
                embed = discord.Embed(
                    title=f"🔱 **{actual_multi} fish caught!**",
                    description=(
                        f"{location_line}"
                        f"{bait_line}"
                        f"rod used: {rod['emoji']} {rod['name']}\n\u200b"
                        + (f"\n*(bag nearly full. only {actual_multi}/{multi} caught)*" if actual_multi < multi else "")
                    ),
                    color=discord.Color.from_rgb(80, 0, 180),
                )
                total_value = 0
                new_entries = []
                for fid in catches:
                    f = FISH[fid]
                    await add_fish(ctx.author.id, fid)
                    first_catch = await record_catch(ctx.author.id, fid)
                    total_value += f["value"]
                    tag = " 📖" if first_catch else ""
                    embed.add_field(
                        name=f"{f['emoji']} {f['name']}{tag}",
                        value=f"{f['tier']} • {f['value']} {QUID_EMOJI}",
                        inline=True,
                    )
                    if f["tier"] == "abyssal":
                        await hooks.on_abyssal_catch(self.bot, ctx.author)
                    if f["tier"].startswith("blazing"):
                        await hooks.on_blazing_catch(self.bot, ctx.author, f["tier"])
                    if first_catch:
                        new_entries.append(fid)

                embed.set_footer(text=f"total sell value: {total_value:,} quid")
                await ctx.send(embed=embed)

                for _ in new_entries:
                    await hooks.on_fishbook_entry(self.bot, ctx.author)

                if rod_id == "dreamsky_trident" and channel_id == SIGWATER_CHANNEL:
                    if random.random() < 0.15:
                        async with db.pool.acquire() as conn:
                            already = await conn.fetchval(
                                "SELECT shark_liver FROM user_unlocks WHERE user_id=$1", ctx.author.id
                            )
                            if not already:
                                await conn.execute(
                                    """
                                    INSERT INTO user_unlocks (user_id, shark_liver)
                                    VALUES ($1, TRUE)
                                    ON CONFLICT (user_id) DO UPDATE SET shark_liver = TRUE
                                    """,
                                    ctx.author.id
                                )
                                await ctx.send(
                                    f"🫁 a **shark liver** surfaces alongside your catch. "
                                    f"key component obtained. (`!craft key`)"
                                )
    
                if channel_id in HELL_CHANNEL_IDS:
                    evil = total_value // 5
                    if evil > 0:
                        async with db.pool.acquire() as conn:
                            await conn.execute(
                                """
                                INSERT INTO evil_quid (user_id, amount)
                                VALUES ($1, $2)
                                ON CONFLICT (user_id) DO UPDATE SET amount = evil_quid.amount + $2
                                """,
                                ctx.author.id, evil
                            )

        finally:
            self.bot._fishing_users.discard(ctx.author.id)

    @commands.command(name="fishbag", aliases=["fb"], help="see your fish", usage="!fishbag")
    async def fishbag(self, ctx):
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT fish_id, quantity FROM fish_inventory WHERE user_id = $1 ORDER BY fish_id",
                ctx.author.id,
            )

        if not rows:
            return await ctx.send("your fish bag is empty. go `!fish`!")

        rod_id = await get_equipped_rod(ctx.author.id)
        rod = RODS.get(rod_id) if rod_id else None

        embed = discord.Embed(
            title=f"🎒 {ctx.author.display_name}'s fish bag",
            color=discord.Color.teal(),
        )

        total_value = 0
        count = 0

        for row in rows:
            if count >= 25:
                break

            fish = FISH.get(row["fish_id"])
            if not fish:
                continue

            qty = row["quantity"]
            val = fish["value"] * qty
            total_value += val

            embed.add_field(
                name=f"{fish['emoji']} {fish['name']} x{qty}",
                value=f"{fish['tier']} • {val} {QUID_EMOJI} total",
                inline=False,
            )

            count += 1

        embed.set_footer(
            text=f"total sell value: {total_value} quid"
            + (f" • rod: {rod['emoji']} {rod['name']}" if rod else "")
        )

        await ctx.send(embed=embed)

    @commands.command(name="bagupgrade", help="upgrade your fish bag capacity", usage="!bagupgrade")
    async def bagupgrade(self, ctx):
        async with db.pool.acquire() as conn:
            level = await conn.fetchval(
                "SELECT fish_bag_upgrade FROM user_unlocks WHERE user_id = $1",
                ctx.author.id
            ) or 0
            quid = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1", ctx.author.id
            ) or 0
            current_count = await get_fish_count(ctx.author.id)

        current_slots, _ = CAPACITY_TIERS[level]
        current_label = f"{current_slots} slots" if current_slots else "unlimited"
        at_max = level >= len(CAPACITY_TIERS) - 1

        tier_lines = []
        for i, (slots, cost) in enumerate(CAPACITY_TIERS):
            slot_label = f"{slots} slots" if slots else "unlimited"
            if i < level:
                tier_lines.append(f"✅ ~~tier {i} - {slot_label}~~")
            elif i == level:
                tier_lines.append(f"**▶ tier {i} - {slot_label}** *(current)*")
            else:
                tier_lines.append(f"🔒 tier {i} - {slot_label} - {cost:,} {QUID_EMOJI}")

        if at_max:
            embed = discord.Embed(
                title="🎒 fish bag - max capacity",
                description=(
                    f"your bag is already at **{current_label}**. nothing left to upgrade.\n\n"
                    + "\n".join(tier_lines)
                ),
                color=discord.Color.gold(),
            )
            embed.set_footer(text=f"fish stored: {current_count} / {current_slots or '∞'}")
            return await ctx.send(embed=embed)

        next_level = level + 1
        next_slots, cost = CAPACITY_TIERS[next_level]
        next_label = f"{next_slots} slots" if next_slots else "unlimited"
        can_afford = quid >= cost
        balance_line = (
            f"✅ balance: **{quid:,} {QUID_EMOJI}** (enough)"
            if can_afford
            else f"❌ balance: **{quid:,} {QUID_EMOJI}** (need {cost - quid:,} more)"
        )

        embed = discord.Embed(
            title="🎒 fish bag upgrade",
            description=(
                f"{balance_line}\n\n"
                + "\n".join(tier_lines)
            ),
            color=discord.Color.teal() if can_afford else discord.Color.red(),
        )
        embed.add_field(
            name="next upgrade",
            value=f"{current_label} -> **{next_label}**  •  costs **{cost:,} {QUID_EMOJI}**",
            inline=False,
        )
        embed.set_footer(text=f"fish stored: {current_count} / {current_slots or '∞'}")

        if not can_afford:
            return await ctx.send(embed=embed)

        view = BagUpgradeView(ctx.author, level, next_level, next_label, cost)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="sell", help="sell all your fish for quid", usage="!sell")
    async def sell(self, ctx):
        import datetime as _dt

        async with db.pool.acquire() as conn:
            last_sell = await conn.fetchval(
                "SELECT last_sell FROM fish_sales WHERE user_id = $1", ctx.author.id
            )
            if last_sell:
                if last_sell.tzinfo is None:
                    last_sell = last_sell.replace(tzinfo=_dt.timezone.utc)
                elapsed = (_dt.datetime.now(_dt.timezone.utc) - last_sell).total_seconds()
                if elapsed < SELL_COOLDOWN_HOURS * 3600:
                    remaining = int(SELL_COOLDOWN_HOURS * 3600 - elapsed)
                    retry_ts = int(_dt.datetime.now(_dt.timezone.utc).timestamp() + remaining)
                    return await ctx.send(
                        f"you can sell again <t:{retry_ts}:R>."
                    )

            rows = await conn.fetch(
                "SELECT fish_id, quantity FROM fish_inventory WHERE user_id = $1",
                ctx.author.id,
            )

            if not rows:
                return await ctx.send("you have no fish to sell.")

            total = sum(
                FISH[r["fish_id"]]["value"] * r["quantity"]
                for r in rows
                if r["fish_id"] in FISH
            )

            await conn.execute(
                "DELETE FROM fish_inventory WHERE user_id = $1", ctx.author.id,
            )

            await conn.execute(
                """
                INSERT INTO economy (user_id, quid)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET quid = economy.quid + $2
                """,
                ctx.author.id, total,
            )

            new_total = await conn.fetchval(
                """
                INSERT INTO fish_sales (user_id, total_sold, last_sell)
                VALUES ($1, $2, NOW())
                ON CONFLICT (user_id) DO UPDATE
                    SET total_sold = fish_sales.total_sold + $2,
                        last_sell = NOW()
                RETURNING total_sold
                """,
                ctx.author.id, total,
            )

        await ctx.send(
            f"🐟 {ctx.author.display_name} sold all their fish for **{total:,} {QUID_EMOJI}**!"
        )

        await hooks.on_fish_sold(self.bot, ctx.author, new_total)

    @commands.command(name="fishbook", aliases=["fishdex", "fd", "dex"], help="view your fish encyclopedia", usage="!fishbook")
    async def fishbook(self, ctx, member: discord.Member = None):
        user = member or ctx.author
        caught = await get_caught_set(user.id)
        view = FishbookView(user, caught)
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="rod", help="view and equip your rods", usage="!rod")
    async def rod_cmd(self, ctx):
        view = await RodView.build(ctx.author)
        if not view.children:
            return await ctx.send("you don't own any rods yet. buy one from `!shop`")
        await ctx.send(embed=view.embed, view=view)

    @commands.command(name="craft", help="craft items", usage="!craft trident | !craft key | !craft pitchfork")
    async def craft(self, ctx, *, item: str = ""):
        item_lower = item.lower().strip()
        if item_lower in ("trident", "dreamsky trident"):
            await self._craft_trident(ctx)
        elif item_lower in ("key", "outlandish key"):
            await self._craft_key(ctx)
        elif item_lower == "pitchfork":
            await self._craft_pitchfork(ctx)
        else:
            await ctx.send(
                "craftable items:\n"
                "• `!craft trident` - dreamsky trident\n"
                "• `!craft key` - outlandish key (unlocks hell)\n"
                "• `!craft pitchfork` - pitchfork (consumes trident, catches blazing fish)"
            )

    async def _craft_trident(self, ctx):
        REQUIRED_RODS = list(SHOP_RODS.keys())
        QUID_COST = 15000
        async with db.pool.acquire() as conn:
            has_soul    = await conn.fetchval("SELECT philosopher_soul FROM user_unlocks WHERE user_id=$1", ctx.author.id) or False
            has_sigshark= await conn.fetchval("SELECT sigshark_rod FROM user_unlocks WHERE user_id=$1", ctx.author.id) or False
            already     = await conn.fetchval("SELECT 1 FROM user_owned_rods WHERE user_id=$1 AND rod_id='dreamsky_trident'", ctx.author.id)
            if already:
                return await ctx.send("you already own the **🔱 dreamsky trident**.")
            owned_ids   = {r["rod_id"] for r in await conn.fetch("SELECT rod_id FROM user_owned_rods WHERE user_id=$1", ctx.author.id)}
            missing     = [r for r in REQUIRED_RODS if r not in owned_ids]
            quid        = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0

        embed = discord.Embed(title="🔱 dreamsky trident craft requirements", color=discord.Color.from_rgb(80, 0, 180))
        embed.add_field(name="rods", value="\n".join(f"{'✅' if r not in missing else '❌'} {RODS[r]['emoji']} {RODS[r]['name']}" for r in REQUIRED_RODS), inline=False)
        embed.add_field(name="🦷 sharkfang rod",    value="✅ obtained" if has_sigshark else "❌ defeat the sigshark in sigwater", inline=False)
        embed.add_field(name="philosopher's soul",   value="✅ obtained" if has_soul    else "❌ defeat socrates in heaven",       inline=False)
        embed.add_field(name=f"{QUID_COST:,} quid", value=f"{'✅' if quid >= QUID_COST else '❌'} you have {quid:,}",             inline=False)

        if missing or not has_sigshark or not has_soul or quid < QUID_COST:
            embed.description = "you don't meet all the requirements yet."
            return await ctx.send(embed=embed)

        async with db.pool.acquire() as conn:
            await conn.execute("UPDATE economy SET quid = quid - $1 WHERE user_id=$2", QUID_COST, ctx.author.id)
            await conn.execute("INSERT INTO user_owned_rods (user_id, rod_id) VALUES ($1, 'dreamsky_trident') ON CONFLICT DO NOTHING", ctx.author.id)
        await set_equipped_rod(ctx.author.id, "dreamsky_trident")
        await ctx.send(embed=discord.Embed(
            title="🔱 dreamsky trident crafted!",
            description=f"**-{QUID_COST:,} {QUID_EMOJI}**\nequipped automatically. catches 5 fish at once.\n\nuse `!craft key` to work towards the outlandish key.",
            color=discord.Color.from_rgb(80, 0, 180)
        ))
        await hooks.on_dreamsky_craft(self.bot, ctx.author)

    async def _craft_key(self, ctx):
        KEY_COMPONENTS = {
            "spark_of_hatred": ("⚡ spark of hatred", "defeat socrates prime in the dream sky (`!fight`)"),
            "shark_liver": ("🫁 shark liver", "fish in sigwater with the dreamsky trident (15%)"),
            "workers_tear": ("😢 worker's tear", "!work in minneapolis (20% chance)"),
            "snow_globe": ("❄️ snow globe", "defeat the yeti in the icy peaks (`!fight`)"),
            "bone_key_cutter": ("🦴 bone key cutter", "defeat vladurk in house of vlads (`!fight`)"),
        }
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT spark_of_hatred, shark_liver, workers_tear, snow_globe, bone_key_cutter, outlandish_key FROM user_unlocks WHERE user_id=$1",
                ctx.author.id
            )
        if row and row["outlandish_key"]:
            return await ctx.send("you already forged the **🗝️ outlandish key**. hell is open to you.")

        have = {k: bool(row[k]) if row else False for k in KEY_COMPONENTS}
        all_have = all(have.values())
        embed = discord.Embed(title="🗝️ outlandish key components", color=discord.Color.gold() if all_have else discord.Color.dark_grey())
        for key, (label, source) in KEY_COMPONENTS.items():
            embed.add_field(name=f"{'✅' if have[key] else '❌'} {label}", value=source, inline=False)

        if not all_have:
            embed.set_footer(text=f"{sum(1 for v in have.values() if not v)} component(s) still needed")
            return await ctx.send(embed=embed)

        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE user_unlocks SET spark_of_hatred=FALSE, shark_liver=FALSE, workers_tear=FALSE, snow_globe=FALSE, bone_key_cutter=FALSE, outlandish_key=TRUE WHERE user_id=$1",
                ctx.author.id
            )
            await conn.execute("INSERT INTO user_inventory (user_id, item_id) VALUES ($1, 'vacation_hell_limbo') ON CONFLICT DO NOTHING", ctx.author.id)

        limbo_role = ctx.guild.get_role(HELL_LAYERS[0]["role"])
        if limbo_role and limbo_role not in ctx.author.roles:
            await ctx.author.add_roles(limbo_role)

        await ctx.send(embed=discord.Embed(
            title="🗝️ OUTLANDISH KEY FORGED",
            description=(
                f"**{ctx.author.display_name}** assembled the key.\n\n"
                "the first gate of hell opens and you descend into limbo.\n\n"
                "use `!fish` to catch blazing fish.\n"
                "complete the layer's mechanic to `!descend`."
            ),
            color=discord.Color.from_rgb(180, 0, 0)
        ))
        await hooks.on_hell_unlocked(self.bot, ctx.author)

    async def _craft_pitchfork(self, ctx):
        async with db.pool.acquire() as conn:
            has_trident = await conn.fetchval("SELECT 1 FROM user_owned_rods WHERE user_id=$1 AND rod_id='dreamsky_trident'", ctx.author.id)
            has_pitchfork = await conn.fetchval("SELECT 1 FROM user_owned_rods WHERE user_id=$1 AND rod_id='pitchfork'", ctx.author.id)
        if not has_trident:
            return await ctx.send("you need the **🔱 dreamsky trident** to forge the pitchfork.")
        if ctx.channel.id not in HELL_CHANNEL_IDS:
            return await ctx.send("you need to be in hell boy")
        if has_pitchfork:
            return await ctx.send("you already own the pitchfork.")

        async with db.pool.acquire() as conn:
            await conn.execute("DELETE FROM user_owned_rods WHERE user_id=$1 AND rod_id='dreamsky_trident'", ctx.author.id)
            await conn.execute("INSERT INTO user_owned_rods (user_id, rod_id) VALUES ($1, 'pitchfork') ON CONFLICT DO NOTHING", ctx.author.id)
        equipped = await get_equipped_rod(ctx.author.id)
        if equipped == "dreamsky_trident":
            await set_equipped_rod(ctx.author.id, "pitchfork")

        await ctx.send(embed=discord.Embed(
            title="🔱 PITCHFORK FORGED",
            description="the dreamsky trident melts into the pitchfork of hell.\n\ncatches **3 fish at once**. only rod that catches **blazing fish**. **no going back.**",
            color=discord.Color.from_rgb(180, 0, 0)
        ))
        await hooks.on_pitchfork_forged(self.bot, ctx.author)

    @commands.command(name="bait", help="view your bait", usage="!bait")
    async def bait_cmd(self, ctx):
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT common_bait, rare_bait, legendary_bait, deep_bait FROM user_bait WHERE user_id = $1",
                ctx.author.id
            )

        embed = discord.Embed(
            title=f"🪱 {ctx.author.display_name}'s bait",
            color=discord.Color.green()
        )

        has_any = row and any(row[b["column"]] > 0 for b in BAIT_ITEMS.values())
        if not has_any:
            embed.description = "you have no bait. buy some from `!shop`"
        else:
            for bait in BAIT_ITEMS.values():
                qty = row[bait["column"]] if row else 0
                if qty > 0:
                    embed.add_field(
                        name=f"{bait['emoji']} {bait['name']} x{qty}",
                        value=bait["description"],
                        inline=False
                    )

        await ctx.send(embed=embed)

class BaitShopButton(discord.ui.Button):
    def __init__(self, bait_id: str, bait: dict):
        super().__init__(
            label=bait["name"],
            style=discord.ButtonStyle.primary,
            custom_id=f"shop_buy_bait_{bait_id}",
        )
        self.bait_id = bait_id
        self.bait = bait

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        bait = self.bait

        async with db.pool.acquire() as conn:
            quid = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1", member.id
            ) or 0

            if quid < bait["price"]:
                return await interaction.response.send_message(
                    "❌ you don't have enough quid", ephemeral=True
                )

            await conn.execute(
                "UPDATE economy SET quid = quid - $1 WHERE user_id = $2",
                bait["price"], member.id,
            )

        await add_bait(member.id, bait["column"])

        await interaction.response.send_message(
            f"✅ bought **{bait['emoji']} {bait['name']}** for {bait['price']} {QUID_EMOJI}",
            ephemeral=True,
        )

class RodEquipButton(discord.ui.Button):
    def __init__(self, rod_id: str, rod: dict, is_equipped: bool):
        super().__init__(
            label=rod["name"],
            emoji=rod["emoji"],
            style=discord.ButtonStyle.success if is_equipped else discord.ButtonStyle.secondary,
            custom_id=f"equip_rod_{rod_id}",
            disabled=is_equipped,
        )
        self.rod_id = rod_id
        self.rod = rod

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.owner_id:
            return await interaction.response.send_message("not your rods", ephemeral=True)

        await set_equipped_rod(interaction.user.id, self.rod_id)

        await interaction.response.send_message(
            f"✅ equipped **{self.rod['emoji']} {self.rod['name']}**",
            ephemeral=True
        )

        new_view = await RodView.build(interaction.user)
        await interaction.message.edit(embed=new_view.embed, view=new_view)


class RodView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=60)
        self.owner_id = owner_id
        self.embed = None

    @classmethod
    async def build(cls, user: discord.Member) -> "RodView":
        view = cls(user.id)
        equipped = await get_equipped_rod(user.id)

        async with db.pool.acquire() as conn:
            has_sigshark = await conn.fetchval(
                "SELECT sigshark_rod FROM user_unlocks WHERE user_id = $1", user.id
            ) or False

        async with db.pool.acquire() as conn:
            owned_rows = await conn.fetch(
                "SELECT rod_id FROM user_owned_rods WHERE user_id = $1", user.id
            )
        owned_ids = {r["rod_id"] for r in owned_rows}
        if has_sigshark:
            owned_ids.add("sigshark_rod")

        owned_rods = {k: v for k, v in RODS.items() if k in owned_ids}

        embed = discord.Embed(
            title=f"🎣 {user.display_name}'s rods",
            color=discord.Color.blurple()
        )

        for rod_id, rod in owned_rods.items():
            is_eq = rod_id == equipped
            tag = " *(equipped)*" if is_eq else ""
            embed.add_field(
                name=f"{rod['emoji']} {rod['name']}{tag}",
                value=rod["description"],
                inline=False
            )
            view.add_item(RodEquipButton(rod_id, rod, is_eq))

        view.embed = embed
        return view

TIER_LABELS = {
    "junk": ("🗑️", "junk"),
    "common": ("🐟", "common"),
    "uncommon": ("🎸", "uncommon"),
    "rare": ("💎", "rare"),
    "legendary": ("🌟", "legendary"),
    "abyssal": ("🕳️", "abyssal"),
    "vacation-sigwater": ("💀", "putrid"),
    "vacation-heaven": ("🕊️", "divine"),
    "vacation-minneapolis": ("🏙️", "classy"),
    "vacation-houseofvlads": ("🦴", "boned"),
    "vacation-dreamsky": ("✨", "ascent"),
    "vacation-icypeaks": ("❄️", "frozen"),
    "blazing-1": ("🌫️", "limbo"),
    "blazing-2": ("❤️‍🔥", "lust"),
    "blazing-3": ("🍖", "gluttony"),
    "blazing-4": ("🪙", "greed"),
    "blazing-5": ("⚡", "wrath"),
    "blazing-6": ("🐐", "heresy"),
    "blazing-7": ("🩸", "violence"),
    "blazing-8": ("🎭", "fraud"),
    "blazing-9": ("🗡️", "treachery"),
}

class FishbookView(discord.ui.View):
    def __init__(self, user: discord.Member, caught: set):
        super().__init__(timeout=60)
        self.user = user
        self.caught = caught
        self.tiers = TIER_ORDER
        self.page = 0
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        self.add_item(FishbookPrevButton(self))
        self.add_item(FishbookNextButton(self))

    def build_embed(self) -> discord.Embed:
        tier = self.tiers[self.page]
        emoji, label = TIER_LABELS[tier]
        fish_in_tier = [(fid, f) for fid, f in FISH.items() if f["tier"] == tier]

        total_fish = len(FISH)
        total_caught = len(self.caught)
        percent = int((total_caught / total_fish) * 100) if total_fish else 0

        embed = discord.Embed(
            title=f"📖 {self.user.display_name}'s fishbook - {emoji} {label}",
            description=f"overall: **{total_caught}/{total_fish}** ({percent}%)",
            color=TIER_COLORS[tier],
        )

        for fish_id, fish in fish_in_tier:
            if fish_id in self.caught:
                embed.add_field(
                    name=f"{fish['emoji']} {fish['name']}",
                    value=f"✅ caught  -  {fish['value']} {QUID_EMOJI}",
                    inline=True,
                )
            else:
                embed.add_field(
                    name="❓ ???",
                    value=f"not yet caught  -  {fish['value']} {QUID_EMOJI}",
                    inline=True,
                )

        embed.set_footer(text=f"page {self.page + 1}/{len(self.tiers)}")
        return embed


class FishbookPrevButton(discord.ui.Button):
    def __init__(self, view: "FishbookView"):
        super().__init__(label="◀", style=discord.ButtonStyle.success, disabled=view.page == 0)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        self.view_ref.page -= 1
        self.view_ref._build_buttons()
        await interaction.response.edit_message(embed=self.view_ref.build_embed(), view=self.view_ref)


class FishbookNextButton(discord.ui.Button):
    def __init__(self, view: "FishbookView"):
        super().__init__(label="▶", style=discord.ButtonStyle.success, disabled=view.page >= len(TIER_ORDER) - 1)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        self.view_ref.page += 1
        self.view_ref._build_buttons()
        await interaction.response.edit_message(embed=self.view_ref.build_embed(), view=self.view_ref)


class BagUpgradeView(discord.ui.View):
    def __init__(self, user: discord.Member, current_level: int, next_level: int, next_label: str, cost: int):
        super().__init__(timeout=30)
        self.user = user
        self.current_level = current_level
        self.next_level = next_level
        self.next_label = next_label
        self.cost = cost

    @discord.ui.button(label="upgrade", style=discord.ButtonStyle.success, emoji="🎒")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("this isn't your bag.", ephemeral=True)

        self.stop()

        async with db.pool.acquire() as conn:
            quid = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1", self.user.id
            ) or 0
            current_level = await conn.fetchval(
                "SELECT fish_bag_upgrade FROM user_unlocks WHERE user_id = $1", self.user.id
            ) or 0

            if current_level != self.current_level:
                return await interaction.response.edit_message(
                    embed=discord.Embed(description="❌ your bag level changed. run `!bagupgrade` again.", color=discord.Color.red()),
                    view=None,
                )
            if quid < self.cost:
                return await interaction.response.edit_message(
                    embed=discord.Embed(description="❌ you no longer have enough quid.", color=discord.Color.red()),
                    view=None,
                )

            await conn.execute(
                "UPDATE economy SET quid = quid - $1 WHERE user_id = $2", self.cost, self.user.id
            )
            await conn.execute(
                """
                INSERT INTO user_unlocks (user_id, fish_bag_upgrade)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET fish_bag_upgrade = $2
                """,
                self.user.id, self.next_level
            )

        embed = discord.Embed(
            title="🎒 bag upgraded!",
            description=(
                f"capacity expanded to **{self.next_label}**.\n"
                f"**-{self.cost:,} {QUID_EMOJI}** spent."
            ),
            color=discord.Color.teal(),
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("this isn't your bag.", ephemeral=True)
        self.stop()
        await interaction.response.edit_message(
            embed=discord.Embed(description="upgrade cancelled.", color=discord.Color.greyple()),
            view=None,
        )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


async def setup(bot):
    await bot.add_cog(FishingCog(bot))