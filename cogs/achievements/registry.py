from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Achievement:
    id: str
    category: str
    name: str
    description: str
    hidden: bool
    target: Optional[int]
    reward_xp: int
    reward_quid: int
    points: int = 0
    hint: Optional[str] = None

BONUS_ACHIEVEMENT_IDS: frozenset[str] = frozenset({
    "economy.tax_collector",
})

ACHIEVEMENTS: dict[str, Achievement] = {
    "xp.level.31": Achievement(
        id="xp.level.31",
        category="xp",
        name="those who know",
        description="get to level 31",
        hidden=False,
        target=31,
        reward_xp=500,
        reward_quid=50,
    ),

    "xp.remove_xp": Achievement(
        id="xp.remove_xp",
        category="xp",
        name="vladbot hater",
        description="remove xp from vladbot",
        hidden=False,
        target=None,
        reward_xp=250,
        reward_quid=25,
    ),

    "economy.fail_crime": Achievement(
        id="economy.fail_crime",
        category="economy",
        name="caught",
        description="fail a crime",
        hidden=False,
        target=None,
        reward_xp=400,
        reward_quid=75,
    ),

    "economy.work.10": Achievement(
        id="economy.work.10",
        category="economy",
        name="lawful",
        description="work 10 times",
        hidden=False,
        target=10,
        reward_xp=650,
        reward_quid=90,
    ),

    "economy.buy_ring": Achievement(
        id="economy.buy_ring",
        category="economy",
        name="ready to propose",
        description="buy an engagement ring",
        hidden=False,
        target=None,
        reward_xp=500,
        reward_quid=100,
    ),

    "economy.daily": Achievement(
        id="economy.daily",
        category="economy",
        name="winner",
        description="claim your daily rewards once",
        hidden=False,
        target=None,
        reward_xp=100,
        reward_quid=100,
    ),

    "economy.weekly": Achievement(
        id="economy.weekly",
        category="economy",
        name="chicken dinner",
        description="claim your weekly rewards once",
        hidden=False,
        target=None,
        reward_xp=100,
        reward_quid=100,
    ),

    "economy.buy_cologne": Achievement(
        id="economy.buy_cologne",
        category="economy",
        name="attracting and repelling",
        description="buy cologne and cover yourself in it",
        hidden=False,
        target=None,
        reward_xp=150,
        reward_quid=90,
    ),

    "economy.work_big": Achievement(
        id="economy.work_big",
        category="economy",
        name="two hundo",
        description="earn 200 quid in a single !work",
        hidden=False,
        target=None,
        reward_xp=500,
        reward_quid=100,
    ),

    "economy.banker": Achievement(
        id="economy.banker",
        category="economy",
        name="actually making bank",
        description="become a vlad banker",
        hidden=False,
        target=None,
        reward_xp=500,
        reward_quid=100,
    ),

    "gambling.dealer": Achievement(
        id="gambling.dealer",
        category="gambling",
        name="bad hand",
        description="beat the dealer at the house game",
        hidden=False,
        target=None,
        reward_xp=500,
        reward_quid=0,
    ),

    "social.married": Achievement(
        id="social.married",
        category="social",
        name="til death do us part",
        description="get married",
        hidden=False,
        target=None,
        reward_xp=500,
        reward_quid=75,
    ),

    "social.jailed": Achievement(
        id="social.jailed",
        category="social",
        name="icemate",
        description="get jailed for committing a crime in minneapolis",
        hidden=True,
        target=None,
        reward_xp=-100,
        reward_quid=50,
        hint="try doing crimes somewhere else"
    ),

    "social.trial": Achievement(
        id="social.trial",
        category="social",
        name="justice for all",
        description="face the mighty judge vladieu in court",
        hidden=False,
        target=None,
        reward_xp=200,
        reward_quid=75
    ),

    "social.vladurk": Achievement(
        id="social.vladurk",
        category="social",
        name="no fuck",
        description="vanquish vladurk",
        hidden=False,
        target=None,
        reward_xp=200,
        reward_quid=500
    ),

    "social.socrates": Achievement(
        id="social.socrates",
        category="social",
        name="know thyself",
        description="answer socrates' questions in heaven",
        hidden=False,
        target=None,
        reward_xp=500,
        reward_quid=0,
    ),

    "vacation.sigwater": Achievement(
        id="vacation.sigwater",
        category="vacation",
        name="putrid guest",
        description="travel to sigwater",
        hidden=False,
        target=None,
        reward_xp=1,
        reward_quid=1,
    ),

    "vacation.houseofvlads": Achievement(
        id="vacation.houseofvlads",
        category="vacation",
        name="boney",
        description="travel to house of vlads",
        hidden=False,
        target=None,
        reward_xp=150,
        reward_quid=75,
    ),

    "vacation.minneapolis": Achievement(
        id="vacation.minneapolis",
        category="vacation",
        name="twin cities",
        description="travel to minneapolis",
        hidden=False,
        target=None,
        reward_xp=100,
        reward_quid=50,
    ),

    "vacation.icypeaks": Achievement(
        id="vacation.icypeaks",
        category="vacation",
        name="glacial ascent",
        description="travel to the icy peaks",
        hidden=False,
        target=None,
        reward_xp=125,
        reward_quid=60,
    ),

    "vacation.heaven": Achievement(
        id="vacation.heaven",
        category="vacation",
        name="past the gates",
        description="travel to heaven",
        hidden=False,
        target=None,
        reward_xp=150,
        reward_quid=75,
    ),

    "fishing.sigshark": Achievement(
        id="fishing.sigshark",
        category="fishing",
        name="conquering the seas",
        description="banish the supreme sigshark into the depths of sigwater",
        hidden=False,
        target=None,
        reward_xp=500,
        reward_quid=500,
    ),

    "fishing.abyssal": Achievement(
        id="fishing.abyssal",
        category="fishing",
        name="from the void",
        description="catch an abyssal fish",
        hidden=True, target=None,
        reward_xp=300, reward_quid=300,
        hint="some rods reach deeper than others"
    ),
    
    "fishing.sell_10k": Achievement(
        id="fishing.sell_10k",
        category="fishing",
        name="fish market",
        description="sell 10,000 quid worth of fish",
        hidden=False, target=None,
        reward_xp=500, reward_quid=250,
    ),

    "fishing.fishbook_complete": Achievement(
        id="fishing.fishbook_complete",
        category="fishing",
        name="marine biologist",
        description="catch every fish in the fishbook",
        hidden=False,
        target=None,
        reward_xp=500,
        reward_quid=200,
    ),

    "fishing.dreamsky": Achievement(
        id="fishing.dreamsky",
        category="fishing",
        name="gift of neptune",
        description="obtain the dreamsky trident",
        hidden=False,
        target=None,
        reward_xp=1000,
        reward_quid=0,
    ),

    "fun.quote": Achievement(
        id="fun.quote",
        category="fun",
        name="philosophical",
        description="quote someone for their wise words",
        hidden=False,
        target=None,
        reward_xp=150,
        reward_quid=50,
    ),

    "fun.wordle": Achievement(
        id="fun.wordle",
        category="fun",
        name="shakespeare",
        description="win a game of wordle",
        hidden=False,
        target=None,
        reward_xp=150,
        reward_quid=50,
    ),

    "dreamsky.ascended": Achievement(id="dreamsky.ascended",category="dreamsky",name="above the clouds",description="ascend to the dream sky",hidden=False,target=None,reward_xp=500,reward_quid=150),
    "dreamsky.socrates_prime": Achievement(id="dreamsky.socrates_prime",category="dreamsky",name="greco",description="defeat socrates prime",hidden=False,target=None,reward_xp=1500,reward_quid=500),
    "dreamsky.pitchfork": Achievement(id="dreamsky.pitchfork",category="dreamsky",name="devil's stick",description="forge the pitchfork by consuming the dreamsky trident",hidden=False,target=None,reward_xp=1000,reward_quid=250),
    "dreamsky.blazing_first": Achievement(id="dreamsky.blazing_first",category="fishing",name="fish on fire",description="catch any blazing fish for the first time",hidden=False,target=None,reward_xp=600,reward_quid=200),
    "dreamsky.blazing_all_tiers": Achievement(id="dreamsky.blazing_all_tiers",category="fishing",name="fish on fire 2",description="catch at least one fish from every blazing tier",hidden=True,target=None,reward_xp=3000,reward_quid=1000,hint="descend all the way and fish in every layer"),
    "hell.workers_tear": Achievement(id="hell.workers_tear",category="dreamsky",name="nine to five",description="obtain the workers tear",hidden=False,target=None,reward_xp=100,reward_quid=95),
    "hell.bone_key_cutter": Achievement(id="hell.bone_key_cutter",category="hell",name="bonebreaker",description="obtain the bone key cutter from vladurk",hidden=False,target=None,reward_xp=300,reward_quid=75),
    "hell.key_forged": Achievement(id="hell.key_forged",category="hell",name="what a key bro",description="forge the outlandish key and unlock hell",hidden=False,target=None,reward_xp=2000,reward_quid=1000),
    "hell.limbo": Achievement(id="hell.limbo",category="hell",name="first circle",description="enter limbo",hidden=False,target=None,reward_xp=300,reward_quid=100),
    "hell.lust": Achievement(id="hell.lust",category="hell",name="second circle",description="descend into lust",hidden=False,target=None,reward_xp=350,reward_quid=120),
    "hell.gluttony": Achievement(id="hell.gluttony",category="hell",name="third circle",description="descend into gluttony",hidden=False,target=None,reward_xp=400,reward_quid=140),
    "hell.greed": Achievement(id="hell.greed",category="hell",name="fourth circle",description="descend into greed",hidden=False,target=None,reward_xp=450,reward_quid=160),
    "hell.wrath": Achievement(id="hell.wrath",category="hell",name="fifth circle",description="descend into wrath",hidden=False,target=None,reward_xp=500,reward_quid=180),
    "hell.heresy": Achievement(id="hell.heresy",category="hell",name="sixth circle",description="descend into heresy",hidden=False,target=None,reward_xp=550,reward_quid=200),
    "hell.violence": Achievement(id="hell.violence",category="hell",name="seventh circle",description="descend into violence",hidden=False,target=None,reward_xp=600,reward_quid=220),
    "hell.fraud": Achievement(id="hell.fraud",category="hell",name="eighth circle",description="descend into fraud",hidden=False,target=None,reward_xp=700,reward_quid=260),
    "hell.treachery": Achievement(id="hell.treachery",category="hell",name="ninth circle",description="descend into treachery",hidden=False,target=None,reward_xp=1000,reward_quid=500),
    "hell.boss.aphrodite": Achievement(id="hell.boss.aphrodite",category="hell",name="resistant",description="resist aphrodite's temptations",hidden=False,target=None,reward_xp=600,reward_quid=200),
    "hell.boss.genghis_khan": Achievement(id="hell.boss.genghis_khan",category="hell",name="mongoloid",description="defeat genghis khan",hidden=False,target=None,reward_xp=800,reward_quid=300),
    "hell.boss.king_minnea": Achievement(id="hell.boss.king_minnea",category="hell",name="crowned",description="defeat king minnea",hidden=False,target=None,reward_xp=900,reward_quid=350),
    "hell.boss.dealer_sr": Achievement(id="hell.boss.dealer_sr",category="hell",name="poker face",description="humiliate dealer sr.",hidden=False,target=None,reward_xp=800,reward_quid=300),
    "hell.full_descent": Achievement(id="hell.full_descent",category="hell",name="hell",description="survive hell",hidden=False,target=None,reward_xp=100,reward_quid=100),

    "finance.first_loan": Achievement(
        id="finance.first_loan",
        category="finance",
        name="the signed debt",
        description="take out your first loan",
        hidden=False,
        target=None,
        reward_xp=200,
        reward_quid=75,
    ),

    "finance.loans_taken": Achievement(
        id="finance.loans_taken",
        category="finance",
        name="i am in need",
        description="take 10 loans",
        hidden=False,
        target=10,
        reward_xp=500,
        reward_quid=150,
    ),

    "finance.loan_repaid": Achievement(
        id="finance.loan_repaid",
        category="finance",
        name="debt free",
        description="fully repay a loan",
        hidden=False,
        target=None,
        reward_xp=300,
        reward_quid=100,
    ),

    "finance.first_cd": Achievement(
        id="finance.first_cd",
        category="finance",
        name="deposit certified",
        description="open your first certificate of deposit",
        hidden=False,
        target=None,
        reward_xp=250,
        reward_quid=75,
    ),

    "finance.cd_claimed": Achievement(
        id="finance.cd_claimed",
        category="finance",
        name="investing yes",
        description="claim a matured cd",
        hidden=False,
        target=None,
        reward_xp=300,
        reward_quid=100,
    ),

    "finance.cd_claimed_count": Achievement(
        id="finance.cd_claimed_count",
        category="finance",
        name="master investor",
        description="claim 10 CDs",
        hidden=False,
        target=10,
        reward_xp=700,
        reward_quid=200,
    ),

    "finance.first_stock": Achievement(
        id="finance.first_stock",
        category="finance",
        name="enter the market",
        description="buy your first stock",
        hidden=False,
        target=None,
        reward_xp=200,
        reward_quid=75,
    ),

    "finance.stocks_bought": Achievement(
        id="finance.stocks_bought",
        category="finance",
        name="share collector",
        description="buy 100 total shares",
        hidden=False,
        target=100,
        reward_xp=600,
        reward_quid=200,
    ),

    "finance.stock_profit": Achievement(
        id="finance.stock_profit",
        category="finance",
        name="stonks",
        description="make a profit from selling stocks",
        hidden=False,
        target=None,
        reward_xp=250,
        reward_quid=100,
    ),

    "finance.stock_loss": Achievement(
        id="finance.stock_loss",
        category="finance",
        name="worst investor ever",
        description="sell a stock at a loss",
        hidden=True,
        target=None,
        reward_xp=150,
        reward_quid=50,
        hint="it'll go back up..."
    ),

    "finance.total_profit": Achievement(
        id="finance.total_profit",
        category="finance",
        name="dream big trade big",
        description="earn 10,000 total profit from stocks",
        hidden=False,
        target=10_000,
        reward_xp=800,
        reward_quid=300,
    ),

    "finance.first_investment": Achievement(
        id="finance.first_investment",
        category="finance",
        name="diversified",
        description="invest in an index fund",
        hidden=False,
        target=None,
        reward_xp=200,
        reward_quid=75,
    ),

    "finance.total_invested": Achievement(
        id="finance.total_invested",
        category="finance",
        name="yeah bitch capitalism",
        description="invest 25,000 total quid",
        hidden=False,
        target=25_000,
        reward_xp=900,
        reward_quid=300,
    ),

    "finance.first_transfer": Achievement(
        id="finance.first_transfer",
        category="finance",
        name="generous",
        description="send quid to another user",
        hidden=False,
        target=None,
        reward_xp=150,
        reward_quid=50,
    ),

    "finance.networth.1k": Achievement(
        id="finance.networth.1k",
        category="finance",
        name="on your feet",
        description="reach 1000 net worth",
        hidden=False,
        target=None,
        reward_xp=200,
        reward_quid=75,
    ),

    "finance.networth.5k": Achievement(
        id="finance.networth.5k",
        category="finance",
        name="moving up",
        description="reach 5000 net worth",
        hidden=False,
        target=None,
        reward_xp=400,
        reward_quid=150,
    ),

    "finance.networth.10k": Achievement(
        id="finance.networth.10k",
        category="finance",
        name="wealthy",
        description="reach 10000 net worth",
        hidden=False,
        target=None,
        reward_xp=700,
        reward_quid=250,
    ),

    "finance.networth.50k": Achievement(
        id="finance.networth.50k",
        category="finance",
        name="tycoon",
        description="reach 50000 net worth",
        hidden=False,
        target=None,
        reward_xp=1500,
        reward_quid=500,
    ),

    "finance.first_crypto": Achievement(
        id="finance.first_crypto",
        category="finance",
        name="THIS is the one",
        description="buy crypto",
        hidden=False,
        target=None,
        reward_xp=100,
        reward_quid=50,
    ),

    "social.adopted_someone": Achievement(
        id="social.adopted_someone",
        category="social",
        name="parent",
        description="adopt someone",
        hidden=False,
        target=None,
        reward_xp=300,
        reward_quid=100,
    ),
 
    "social.first_gift": Achievement(
        id="social.first_gift",
        category="social",
        name="generous stranger",
        description="send someone a gift",
        hidden=False,
        target=None,
        reward_xp=150,
        reward_quid=50,
    ),
 
    "social.first_gift_received": Achievement(
        id="social.first_gift_received",
        category="social",
        name="well liked",
        description="receive your first gift",
        hidden=False,
        target=None,
        reward_xp=100,
        reward_quid=50,
    ),
 
    "social.sent_skull": Achievement(
        id="social.sent_skull",
        category="social",
        name="a message",
        description="gift someone a skull",
        hidden=True,
        target=None,
        reward_xp=100,
        reward_quid=25,
        hint="would bones make a good gift?",
    ),
 
    "social.sent_diamond": Achievement(
        id="social.sent_diamond",
        category="social",
        name="no expense spared",
        description="gift someone a diamond",
        hidden=False,
        target=None,
        reward_xp=500,
        reward_quid=200,
    ),
 
    "social.first_rep_given": Achievement(
        id="social.first_rep_given",
        category="social",
        name="endorsement",
        description="give rep to someone for the first time",
        hidden=False,
        target=None,
        reward_xp=100,
        reward_quid=25,
    ),
 
    "social.wrote_will": Achievement(
        id="social.wrote_will",
        category="social",
        name="last wishes",
        description="write a will",
        hidden=False,
        target=None,
        reward_xp=150,
        reward_quid=50,
    ),

    "pets.first_adopt": Achievement(
        id="pets.first_adopt",
        category="pets",
        name="first companion",
        description="adopt your first pet",
        hidden=False,
        target=None,
        reward_xp=100,
        reward_quid=50,
    ),

    "pets.first_feed": Achievement(
        id="pets.first_feed",
        category="pets",
        name="caregiver",
        description="feed your pet for the first time",
        hidden=False,
        target=None,
        reward_xp=75,
        reward_quid=25,
    ),

    "pets.first_purchase": Achievement(
        id="pets.first_purchase",
        category="pets",
        name="spoiled already",
        description="buy your first pet item",
        hidden=False,
        target=None,
        reward_xp=75,
        reward_quid=25,
    ),

    "pets.first_trick": Achievement(
        id="pets.first_trick",
        category="pets",
        name="roll over",
        description="teach your pet its first trick",
        hidden=False,
        target=None,
        reward_xp=100,
        reward_quid=40,
    ),

    "pets.all_tricks": Achievement(
        id="pets.all_tricks",
        category="pets",
        name="master trainer",
        description="teach your pet every trick",
        hidden=False,
        target=None,
        reward_xp=300,
        reward_quid=150,
    ),

    "pets.level_10": Achievement(
        id="pets.level_10",
        category="pets",
        name="growing up",
        description="reach level 10 with your pet",
        hidden=False,
        target=None,
        reward_xp=150,
        reward_quid=75,
    ),

    "pets.level_20": Achievement(
        id="pets.level_20",
        category="pets",
        name="growing up pt. 2",
        description="reach level 20 with your pet",
        hidden=False,
        target=None,
        reward_xp=300,
        reward_quid=150,
    ),

    "pets.max_level": Achievement(
        id="pets.max_level",
        category="pets",
        name="grew up",
        description="reach the maximum pet level",
        hidden=False,
        target=None,
        reward_xp=500,
        reward_quid=300,
    ),

    "economy.tax_collector": Achievement(
        id="economy.tax_collector",
        category="economy",
        name="tax exempt",
        description="defeat the tax collector",
        hidden=True,
        target=None,
        reward_xp=2500,
        reward_quid=5000,
        hint="find a golden receipt somewhere expensive",
    ),
#    "guards.grumpy_guard": Achievement(
#        id="guards.grumpy_guard",
#        category="guards",
#        name="through the hallway",
#        description="defeat the grumpy guard",
#        hidden=False,
#        target=None,
#        reward_xp=300,
#        reward_quid=100,
#    ),
#
#    "guards.ungrumpy_guard": Achievement(
#        id="guards.ungrumpy_guard",
#        category="guards",
#        name="into the office",
#        description="defeat the ungrumpy guard",
#        hidden=False,
#        target=None,
#        reward_xp=400,
#        reward_quid=150,
#    ),
#
#    "guards.security_system": Achievement(
#        id="guards.security_system",
#        category="guards",
#        name="breach",
#        description="defeat vladbot's security system",
#        hidden=False,
#        target=None,
#        reward_xp=600,
#        reward_quid=250,
#    ),
#
#    "guards.vladbot": Achievement(
#        id="guards.vladbot",
#        category="guards",
#        name="vladbot",
#        description="defeat vladbot",
#        hidden=False,
#        target=None,
#        reward_xp=1000,
#        reward_quid=500,
#    ),
#
#    "guards.arg_stage_1": Achievement(
#        id="guards.arg_stage_1",
#        category="guards",
#        name="cracking me up",
#        description="???",
#        hidden=True,
#        target=None,
#        reward_xp=100,
#        reward_quid=0
#    ),
#
#    "guards.arg_stage_2": Achievement(
#        id="guards.arg_stage_2",
#        category="guards",
#        name="decode",
#        description="???",
#        hidden=True,
#        target=None,
#        reward_xp=150,
#        reward_quid=0,
#    ),
#
#    "guards.arg_stage_3": Achievement(
#        id="guards.arg_stage_3",
#        category="guards",
#        name="deeper",
#        description="???",
#        hidden=True,
#       target=None,
#        reward_xp=200,
#        reward_quid=0,
#    ),
#
#    "guards.arg_stage_4": Achievement(
#        id="guards.arg_stage_4",
#        category="guards",
#        name="look at the sky",
#        description="???",
#        hidden=True,
#        target=None,
#        reward_xp=250,
#        reward_quid=0,
#    ),
#
#    "guards.arg_stage_5": Achievement(
#        id="guards.arg_stage_5",
#        category="guards",
#        name="ethel",
#        description="???",
#        hidden=True,
#        target=None,
#        reward_xp=300,
#        reward_quid=0,
#    ),
#
#    "guards.arg_complete": Achievement(
#        id="guards.arg_complete",
#        category="guards",
#        name="the order of vlads",
#        description="uncover the full history of vladia",
#        hidden=True,
#        target=None,
#        reward_xp=1000,
#        reward_quid=1000,
#    ),
}