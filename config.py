import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.yml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

ECONOMY = CONFIG["economy"]
JAIL_ROLE_ID = ECONOMY["roles"].get("jail")
POLICE_JAIL_ROLE_ID = ECONOMY["roles"].get("vacationjail")
LOTTERY_ROLE_ID = ECONOMY["roles"].get("lottery")
LOTTERY_CHANNEL_ID = ECONOMY["channels"].get("lottery")
XP_PER_QUID = ECONOMY["currency"]["xp_per_quid"]
QUID_EMOJI = ECONOMY["currency"].get("quid_emoji", "")
EVIL_EMOJI = ECONOMY["currency"].get("evil_quid_emoji", "")
JAIL_ENABLED = ECONOMY["jail"].get("enabled", False)
JAIL_DAYS = ECONOMY["jail"]["days"]
LOTTERY_ENABLED = ECONOMY["lottery"].get("enabled", False)
LOTTERY_DAYS = ECONOMY["lottery"]["days"]
LOTTERY_TICKET_PRICE = ECONOMY["lottery"]["ticket_price"]

XP = CONFIG.get("xp", {})
XP_MIN = XP.get("min_xp", 8)
XP_MAX = XP.get("max_xp", 15)
XP_LEVEL_UPS_CHANNEL = XP.get("level_ups_channel")
XP_LAST_EMOJI = XP.get("last_emoji", "")
_raw_rewards = XP.get("level_rewards") or []
XP_LEVEL_REWARDS = sorted(
    _raw_rewards,
    key=lambda r: r.get("level", 0)
)

RESPONSES = CONFIG.get("responses", {})
RESP_ANSWERS = RESPONSES.get("answers") or []
RESP_WHO = RESPONSES.get("who") or []
RESP_WHAT = RESPONSES.get("what") or []
RESP_WHEN = RESPONSES.get("when") or []
RESP_SHOULD = RESPONSES.get("should") or []
RESP_WHY = RESPONSES.get("why") or []

EVENTS = CONFIG["messageevents"]
SIGWATER_CHANNEL = EVENTS.get("sigwaterch")
SIGWATER_ROLE = EVENTS.get("sigwaterrole")
HEAVEN_CHANNEL = EVENTS.get("heavench")
HEAVEN_ROLE = EVENTS.get("heavenrole")
ICY_PEAKS_CHANNEL = EVENTS.get("icypeaksch")
ICY_PEAKS_ROLE = EVENTS.get("icypeaksrole")
MINNEAPOLIS_CHANNEL = EVENTS.get("minneapolisch")
MINNEAPOLIS_ROLE = EVENTS.get("minneapolisrole")
HOUSEOFVLADS_CHANNEL = EVENTS.get("houseofvladsch")
TAX_COLLECTOR_CHANNEL = EVENTS.get("taxch")
TAX_COLLECTOR_ROLE = EVENTS.get("taxrole")

MISC = CONFIG["misc"]
GENERAL_CHANNEL_ID = MISC.get("generalch")
DREAMSKY_CHANNEL = MISC.get("dreamskych")
DREAMSKY_ROLE = MISC.get("dreamskyrole")
SOCIAL_CATEGORY_ID = MISC.get("socialcatg")

HELL = CONFIG["hell"]
HELL_LIMBO = HELL.get("limbo")
HELL_LUST = HELL.get("lust")
HELL_GLUTTONY = HELL.get("gluttony")
HELL_GREED = HELL.get("greed")
HELL_WRATH = HELL.get("wrath")
HELL_HERESY = HELL.get("heresy")
HELL_VIOLENCE = HELL.get("violence")
HELL_FRAUD = HELL.get("fraud")
HELL_TREACHERY = HELL.get("treachery")
HELL_LIMBO_ROLE = HELL.get("limborole")
HELL_LUST_ROLE = HELL.get("lustrole")
HELL_GLUTTONY_ROLE = HELL.get("gluttonyrole")
HELL_GREED_ROLE = HELL.get("greedrole")
HELL_WRATH_ROLE = HELL.get("wrathrole")
HELL_HERESY_ROLE = HELL.get("heresyrole")
HELL_VIOLENCE_ROLE = HELL.get("violencerole")
HELL_FRAUD_ROLE = HELL.get("fraudrole")
HELL_TREACHERY_ROLE = HELL.get("treacheryrole")

PARTHENON = CONFIG["parthenon"]
PARTHENON_CHANNEL = PARTHENON.get("parthenonch")
PARTHENON_ROLE = PARTHENON.get("parthenonrole")
KEY_CHANNEL = PARTHENON.get("keych")
BATTLE_REWARD_QUID = PARTHENON.get("reward_quid")
BATTLE_REWARD_XP = PARTHENON.get("reward_xp")