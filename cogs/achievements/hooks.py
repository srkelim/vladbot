from cogs.achievements.manager import AchievementManager

async def on_quote(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="fun.quote"
    )

async def on_wordle(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="fun.wordle"
    )

async def on_level_up(bot, member, level: int):
    if level < 31:
        return

    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="xp.level.31"
    )

async def on_remove_xp_from_vladbot(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="xp.remove_xp"
    )

async def on_crime_failed(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="economy.fail_crime"
    )

async def on_work(bot, member):
    mgr = AchievementManager(bot)
    await mgr.increment_progress(
        user=member,
        achievement_id="economy.work.10",
        amount=1
    )

async def on_work_big(bot, member, earnings: int):
    if earnings < 200:
        return
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="economy.work_big"
    )

async def on_buy_ring(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="economy.buy_ring"
    )

async def on_claim_daily(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="economy.daily"
    )

async def on_buy_cologne(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="economy.buy_cologne"
    )

async def on_marriage(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="social.married"
    )


async def on_jailed(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="social.jailed"
    )

async def on_court(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="social.trial"
    )

async def on_vlad_defeat(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="social.vladurk"
    )

async def on_sigshark_defeat(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="fishing.sigshark"
    )

async def on_dealer_defeat(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="gambling.dealer"
    )

async def on_abyssal_catch(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="fishing.abyssal"
    )
 
async def on_fish_sold(bot, member, total_sold: int):
    if total_sold < 10000:
        return
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="fishing.sell_10k"
    )

async def on_dreamsky_craft(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="fishing.dreamsky"
    )
 
async def on_socrates_defeat(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="social.socrates"
    )

async def on_fishbook_entry(bot, member):
    from cogs.fishing.fishingcommands import FISH, get_caught_set
    caught = await get_caught_set(member.id)
    if len(caught) >= len(FISH):
        mgr = AchievementManager(bot)
        await mgr.unlock(user=member, achievement_id="fishing.fishbook_complete")

async def on_visit_vacation(bot, member, place: str):
    mgr = AchievementManager(bot)

    place = place.lower()

    mapping = {
        "sigwater": "vacation.sigwater",
        "houseofvlads": "vacation.houseofvlads",
        "minneapolis": "vacation.minneapolis",
        "icypeaks": "vacation.icypeaks",
        "heaven": "vacation.heaven",
    }

    achievement_id = mapping.get(place)
    if not achievement_id:
        return

    await mgr.unlock(
        user=member,
        achievement_id=achievement_id
    )

# 1.6

async def on_claim_weekly(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="economy.weekly"
    )

async def on_banker(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(
        user=member,
        achievement_id="economy.banker"
    )

async def on_ascend(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="dreamsky.ascended")
 
async def on_socrates_prime_defeat(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="dreamsky.socrates_prime")
    await mgr.unlock(user=member, achievement_id="hell.spark_of_hatred")
 
async def on_pitchfork_forged(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="dreamsky.pitchfork")
 
async def on_blazing_catch(bot, member, tier: str):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="dreamsky.blazing_first")
    from db import db
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("SELECT fish_id FROM fish_caught WHERE user_id=$1", member.id)
    from cogs.fishing.fishingcommands import FISH
    caught_ids = {r["fish_id"] for r in rows}
    all_blazing = {f"blazing-{i}" for i in range(1, 10)}
    caught_tiers = {FISH[fid]["tier"] for fid in caught_ids if fid in FISH and FISH[fid]["tier"].startswith("blazing")}
    if all_blazing.issubset(caught_tiers):
        await mgr.unlock(user=member, achievement_id="dreamsky.blazing_all_tiers")

async def on_shark_liver(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="hell.shark_liver")
 
async def on_workers_tear(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="hell.workers_tear")
 
async def on_yeti_defeat(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="hell.snow_globe")
 
async def on_vladurk_drop(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="hell.bone_key_cutter")

async def on_hell_unlocked(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="hell.key_forged")
    await mgr.unlock(user=member, achievement_id="hell.limbo")
 
async def on_hell_descend(bot, member, layer_name: str):
    mgr = AchievementManager(bot)
    ach_id = f"hell.{layer_name}"
    try:
        await mgr.unlock(user=member, achievement_id=ach_id)
    except RuntimeError:
        pass
 
async def on_hell_boss_defeat(bot, member, layer_name: str):
    mgr = AchievementManager(bot)
    boss_map = {
        "lust":     "hell.boss.aphrodite",
        "wrath":    "hell.boss.genghis_khan",
        "heresy":   "hell.boss.caligula",
        "violence": "hell.boss.king_minnea",
        "fraud":    "hell.boss.dealer_sr",
    }
    mechanic_map = {
        "limbo":    "hell.limbo_cleared",
        "gluttony": "hell.gluttony_cleared",
        "greed":    "hell.greed_cleared",
    }
    ach_id = boss_map.get(layer_name) or mechanic_map.get(layer_name)
    if ach_id:
        try:
            await mgr.unlock(user=member, achievement_id=ach_id)
        except RuntimeError:
            pass
 
async def on_anti_vlad_joined(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="hell.boss.anti_vlad_joined")
 
async def on_anti_vlad_won(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="hell.boss.anti_vlad_won")
 
async def on_full_descent(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="hell.full_descent")

async def parthenon(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="parthenon.clear")

async def on_tax_collector_defeat(bot, member):
    mgr = AchievementManager(bot)
    await mgr.unlock(user=member, achievement_id="economy.tax_collector")