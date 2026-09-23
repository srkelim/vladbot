import discord
from discord.ext import commands, tasks
import random
import datetime
import asyncio
import math

from db import db
from config import QUID_EMOJI
from cogs.achievements import hooks as ach_hooks

INTEREST_RATE_SAVINGS = 0.015
INTEREST_RATE_LOAN = 0.06
MAX_LOAN_MULTIPLIER = 2 
MAX_LOAN_HARD_CAP = 8_000
LOAN_MIN = 50
CD_MULTIPLIER = 0.06
CD_TERM_HOURS = 24
MARGIN_INTEREST_DAY = 0.03
PORTFOLIO_MAX_STOCKS = 6
MARGIN_MULTIPLIER   = 2.0 
TAX_BRACKETS = [
    (5_000,        0.08),
    (20_000,       0.18),
    (float("inf"), 0.32),
]
SHORT_TERM_TAX_RATE  = 0.40
STAMP_DUTY_RATE      = 0.015
WEALTH_TAX_THRESHOLD = 30_000
WEALTH_TAX_RATE      = 0.015
OPTION_EXPIRY_HOURS = 48
OPTION_CONTRACT_SIZE = 10
INSURANCE_WEEKLY_PREMIUM_RATE = 0.02
INSURANCE_PAYOUT_RATE = 0.60
FINANCE_ANN_ID: int = 1501322474523197531

STOCKS: dict[str, dict] = {
    "VLAD": {"name": "vladcorp", "price": 100, "volatility": 0.05, "emoji": "👑"},
    "FISH": {"name": "sigfish inc.", "price":  30, "volatility": 0.08, "emoji": "🐟"},
    "CALC": {"name": "slang for calculus", "price": 140, "volatility": 0.04, "emoji": "💻"},
    "HELL": {"name": "nestle", "price":  55, "volatility": 0.10, "emoji": "🔥"},
    "DESH": {"name": "joe metri desh corp", "price":  85, "volatility": 0.07, "emoji": "🧊"},
    "VILT": {"name": "viltrum empire", "price": 210, "volatility": 0.03, "emoji": "💰"},
    "DOOF": {"name": "doofenshmirtz evil inc.", "price":  40, "volatility": 0.13, "emoji": "🚓"},
    "HEAV": {"name": "heavenly goods", "price": 350, "volatility": 0.02, "emoji": "☁️"},
}

INDEX_FUNDS: dict[str, dict] = {
    "ISRL": {"name": "israeli fund", "daily_rate": 0.004, "min_invest": 2000, "emoji": "🛡️",
             "description": "0.4% daily return. stable."},
    "GROW": {"name": "growth fund", "daily_rate": 0.012, "min_invest": 500, "emoji": "📈",
             "description": "1.2% daily return but crashes 10% every monday."},
    "VLDB": {"name": "vladbot fund", "daily_rate": 0.00,  "min_invest": 100, "emoji": "🎲",
             "description": "50% chance of +5% daily, 50% chance of -4%."},
    "BLOW": {"name": "blow up fund", "daily_rate": 0.003, "min_invest": 300, "emoji": "📜",
             "description": "0.3% guaranteed daily. very boring. very safe."},
}

def _tax_on_profit(profit: int, held_seconds: float = None) -> int:
    if profit <= 0:
        return 0
    if held_seconds is not None and held_seconds < 86400:
        return int(profit * SHORT_TERM_TAX_RATE)
    for threshold, rate in TAX_BRACKETS:
        if profit < threshold:
            return int(profit * rate)
    return int(profit * TAX_BRACKETS[-1][1])

async def get_balance(user_id: int) -> int:
    async with db.pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT quid FROM economy WHERE user_id=$1", user_id
        ) or 0

async def add_quid(conn, user_id: int, amount: int):
    await conn.execute(
        "INSERT INTO economy (user_id, quid) VALUES ($1, $2) "
        "ON CONFLICT (user_id) DO UPDATE SET quid = economy.quid + $2",
        user_id, amount
    )

async def get_bank_row(conn, user_id: int):
    return await conn.fetchrow(
        "SELECT * FROM finance_bank WHERE user_id=$1", user_id
    )

async def ensure_bank(conn, user_id: int):
    await conn.execute(
        "INSERT INTO finance_bank (user_id, savings, loan_amount, loan_taken_at, cd_amount, cd_matures_at) "
        "VALUES ($1, 0, 0, NULL, 0, NULL) ON CONFLICT DO NOTHING",
        user_id
    )

async def get_stock_price(ticker: str) -> int:
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT price FROM finance_stock_prices WHERE ticker=$1", ticker)
        if row:
            return row["price"]
        return STOCKS[ticker]["price"]

async def get_portfolio(conn, user_id: int) -> list:
    return await conn.fetch(
        "SELECT ticker, shares FROM finance_portfolio WHERE user_id=$1", user_id
    )

async def _fire(bot, user, achievement_id: str):
    try:
        await bot.achievement_manager.unlock(user=user, achievement_id=achievement_id)
    except Exception as e:
        print(f"[_fire] failed to unlock {achievement_id} for {user.id}: {e}")

async def _progress(bot, user, achievement_id: str, amount: int = 1):
    try:
        await bot.achievement_manager.increment_progress(user=user, achievement_id=achievement_id, amount=amount)
    except Exception:
        pass

def _pct(change: float) -> str:
    sign = "+" if change >= 0 else ""
    return f"{sign}{change*100:.2f}%"

def _bar(change: float, width: int = 8) -> str:
    filled = min(width, max(0, round(abs(change) * width / 0.25)))
    char   = "█" if change >= 0 else "▓"
    return char * filled + "░" * (width - filled)

def _stock_embed(results: list[dict]) -> discord.Embed:
    avg_chg = sum(r["change_frac"] for r in results) / len(results) if results else 0
    if avg_chg > 0.03:
        mood, mood_color = "🚀 bull run", discord.Color.from_str("#00e676")
    elif avg_chg > 0:
        mood, mood_color = "📈 slightly up", discord.Color.green()
    elif avg_chg > -0.03:
        mood, mood_color = "📉 slightly down", discord.Color.orange()
    else:
        mood, mood_color = "💀 dead market", discord.Color.red()

    embed = discord.Embed(
        title=f"hourly stock update · {mood}",
        color=mood_color,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text="prices update every hour • use !market to browse • profits taxed")

    lines = []
    for r in sorted(results, key=lambda x: x["change_frac"], reverse=True):
        info  = STOCKS[r["ticker"]]
        arrow = "▲" if r["change_frac"] >= 0 else "▼"
        lines.append(
            f"{info['emoji']} **{r['ticker']}** {arrow} `{r['new_price']:>4}` {QUID_EMOJI}"
            f"`{_pct(r['change_frac']):>7}`  `{_bar(r['change_frac'])}`"
        )
    embed.description = "\n".join(lines)

    gainers = [r for r in results if r["change_frac"] >= 0]
    losers = [r for r in results if r["change_frac"] <  0]
    if gainers:
        best = max(gainers, key=lambda x: x["change_frac"])
        embed.add_field(name="🏆 top gainer",
                        value=f"**{best['ticker']}** {_pct(best['change_frac'])} ({best['old_price']}->{best['new_price']} {QUID_EMOJI})",
                        inline=True)
    if losers:
        worst = min(losers, key=lambda x: x["change_frac"])
        embed.add_field(name="📛 biggest drop",
                        value=f"**{worst['ticker']}** {_pct(worst['change_frac'])} ({worst['old_price']}->{worst['new_price']} {QUID_EMOJI})",
                        inline=True)
    return embed

def _fund_embed(results: list[dict], is_crash_day: bool) -> discord.Embed:
    total_before = sum(r["total_before"] for r in results)
    total_after = sum(r["total_after"]  for r in results)
    net_gain = total_after - total_before

    color = discord.Color.green() if net_gain >= 0 else discord.Color.red()
    title = "📊 daily fund report"
    if is_crash_day:
        title += " · ⚠️ crash day (GROW hit -10%)"

    embed = discord.Embed(title=title, color=color, timestamp=discord.utils.utcnow())
    embed.set_footer(text="use !funds • !invest <FUND> <amount> • !divest <FUND>")

    lines = []
    for r in results:
        sign = "+" if r["gain"] >= 0 else ""
        pct = (r["gain"] / r["total_before"] * 100) if r["total_before"] else 0
        arrow = "▲" if r["gain"] >= 0 else "▼"
        lines.append(
            f"{r['emoji']} **{r['fund_id']}** - {r['name']}\n"
            f"  pool: `{r['total_before']:,}` -> `{r['total_after']:,}` {QUID_EMOJI}"
            f" {arrow} `{sign}{r['gain']:,}` (`{sign}{pct:.2f}%`)"
        )
    embed.description = "\n\n".join(lines) if lines else "no active investments today."

    sign_net = "+" if net_gain >= 0 else ""
    embed.add_field(name="total pool movement",
                    value=f"`{sign_net}{net_gain:,}` {QUID_EMOJI}", inline=False)
    return embed

class ConfirmView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=30)
        self.author_id = author_id
        self.confirmed = False

    @discord.ui.button(label="confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("not your transaction", ephemeral=True)
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="cancelled.", view=None, embed=None)


class StockMarketView(discord.ui.View):
    def __init__(self, bot, prices: dict[str, int]):
        super().__init__(timeout=60)
        self.bot = bot
        self.prices = prices
        self.page = 0
        self.tickers = list(STOCKS.keys())
        self.per_page = 4

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title="📊 stock market", color=discord.Color.green())
        start = self.page * self.per_page
        chunk = self.tickers[start:start + self.per_page]
        for ticker in chunk:
            info = STOCKS[ticker]
            price = self.prices.get(ticker, info["price"])
            embed.add_field(
                name=f"{info['emoji']} **{ticker}** - {info['name']}",
                value=(
                    f"**{price} {QUID_EMOJI}** per share  |  "
                    f"volatility {int(info['volatility']*100)}%  |  "
                    f"⚠️ profits taxed"
                ),
                inline=False
            )
        total = math.ceil(len(self.tickers) / self.per_page)
        embed.set_footer(text=f"page {self.page+1}/{total} • prices update hourly • use !buy <TICKER> <shares>")
        return embed

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        total = math.ceil(len(self.tickers) / self.per_page)
        if self.page < total - 1:
            self.page += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

class PortfolioView(discord.ui.View):
    def __init__(self, bot, user, rows, prices):
        super().__init__(timeout=60)
        self.bot = bot
        self.user = user
        self.rows = rows
        self.prices = prices

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title=f"📁 {self.user.display_name}'s portfolio", color=discord.Color.blurple())
        total_value = 0
        for row in self.rows:
            ticker = row["ticker"]
            shares = row["shares"]
            price = self.prices.get(ticker, STOCKS.get(ticker, {}).get("price", 0))
            val = shares * price
            total_value += val
            info = STOCKS.get(ticker, {})
            embed.add_field(
                name=f"{info.get('emoji','📈')} **{ticker}** x {shares}",
                value=f"{price} {QUID_EMOJI}/share -> **{val} {QUID_EMOJI}** total",
                inline=False
            )
        if not self.rows:
            embed.description = "you own no stocks. use `!buy <ticker> <shares>` to start."
        else:
            embed.add_field(name="total value", value=f"**{total_value} {QUID_EMOJI}**", inline=False)
        return embed

class FinanceCommands(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.market_tick.start()
        self.loan_interest.start()
        self.index_fund_tick.start()
        self.margin_interest.start()
        self.insurance_premium.start()
        self.tax_drain.start()

    def cog_unload(self):
        self.market_tick.cancel()
        self.loan_interest.cancel()
        self.index_fund_tick.cancel()
        self.margin_interest.cancel()
        self.insurance_premium.cancel()
        self.tax_drain.cancel()

    def _ann_channel(self) -> discord.TextChannel | None:
        if not FINANCE_ANN_ID:
            return None
        return self.bot.get_channel(FINANCE_ANN_ID)

    @tasks.loop(hours=1)
    async def market_tick(self):
        await self.bot.wait_until_ready()
        results = []
        MIN_PRICE = 12
        async with db.pool.acquire() as conn:
            for ticker, info in STOCKS.items():
                base_price = info["price"]
                current = await conn.fetchval(
                    "SELECT price FROM finance_stock_prices WHERE ticker=$1", ticker
                ) or base_price

                frac = await conn.fetchval(
                    "SELECT frac FROM finance_stock_frac WHERE ticker=$1", ticker
                ) or 0.0

                change = random.gauss(0, info["volatility"])

                deviation = (current - base_price) / max(base_price, 1)
                reversion_strength = 0.04 + 0.06 * max(0.0, -deviation)
                reversion = -deviation * reversion_strength
                effective_change = change + reversion

                float_price = current + frac + current * effective_change
                float_price = max(MIN_PRICE + 0.01, float_price)

                new_price = int(float_price)
                new_frac  = float_price - new_price

                if new_price <= MIN_PRICE:
                    new_price = MIN_PRICE + 1
                    new_frac  = 0.0

                await conn.execute(
                    "INSERT INTO finance_stock_prices (ticker, price) VALUES ($1,$2) "
                    "ON CONFLICT (ticker) DO UPDATE SET price=$2",
                    ticker, new_price
                )
                await conn.execute(
                    "INSERT INTO finance_stock_frac (ticker, frac) VALUES ($1,$2) "
                    "ON CONFLICT (ticker) DO UPDATE SET frac=$2",
                    ticker, new_frac
                )
                results.append({"ticker": ticker, "old_price": current,
                                 "new_price": new_price,
                                 "change_frac": (new_price - current) / max(current, 1)})
        channel = self._ann_channel()
        if channel:
            await channel.send(embed=_stock_embed(results))

    @tasks.loop(hours=24)
    async def loan_interest(self):
        await self.bot.wait_until_ready()
        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, loan_amount FROM finance_bank WHERE loan_amount > 0")
            for row in rows:
                interest = max(1, int(row["loan_amount"] * INTEREST_RATE_LOAN))
                await conn.execute(
                    "UPDATE finance_bank SET loan_amount=loan_amount+$1 WHERE user_id=$2",
                    interest, row["user_id"]
                )

    @tasks.loop(hours=24)
    async def margin_interest(self):
        """Charge daily interest on any open margin positions."""
        await self.bot.wait_until_ready()
        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, margin_used FROM finance_margin WHERE margin_used > 0")
            for row in rows:
                fee = max(1, int(row["margin_used"] * MARGIN_INTEREST_DAY))
                wallet = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", row["user_id"]) or 0
                deduct = min(fee, wallet)
                if deduct > 0:
                    await conn.execute("UPDATE economy SET quid=quid-$1 WHERE user_id=$2", deduct, row["user_id"])

    @tasks.loop(hours=24 * 7)
    async def insurance_premium(self):
        """Charge weekly insurance premiums."""
        await self.bot.wait_until_ready()
        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id FROM finance_insurance WHERE active=TRUE")
            for row in rows:
                uid = row["user_id"]
                stock_rows = await conn.fetch("SELECT ticker, shares FROM finance_portfolio WHERE user_id=$1", uid)
                portfolio_val = 0
                for sr in stock_rows:
                    p = await conn.fetchval("SELECT price FROM finance_stock_prices WHERE ticker=$1", sr["ticker"]) or 0
                    portfolio_val += p * sr["shares"]
                premium = max(50, int(portfolio_val * INSURANCE_WEEKLY_PREMIUM_RATE))
                wallet  = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", uid) or 0
                if wallet >= premium:
                    await conn.execute("UPDATE economy SET quid=quid-$1 WHERE user_id=$2", premium, uid)
                else:
                    await conn.execute("UPDATE finance_insurance SET active=FALSE WHERE user_id=$1", uid)

    @tasks.loop(hours=24)
    async def index_fund_tick(self):
        await self.bot.wait_until_ready()
        today_is_crash_day = datetime.datetime.utcnow().weekday() == 0
        fund_summaries: dict[str, dict] = {}

        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, fund, amount FROM finance_index_investments")
            for row in rows:
                fund = INDEX_FUNDS.get(row["fund"])
                if not fund:
                    continue
                amount = row["amount"]
                uid = row["user_id"]
                fid = row["fund"]

                if fid == "VLDB":
                    gain = int(amount * 0.05) if random.random() < 0.5 else -int(amount * 0.04)
                elif fid == "GROW" and today_is_crash_day:
                    gain = -int(amount * 0.10)
                else:
                    gain = int(amount * fund["daily_rate"])

                new_amount = max(0, amount + gain)
                await conn.execute(
                    "UPDATE finance_index_investments SET amount=$1 WHERE user_id=$2 AND fund=$3",
                    new_amount, uid, fid
                )

                if fid not in fund_summaries:
                    fund_summaries[fid] = {"fund_id": fid, "name": fund["name"],
                                           "emoji": fund["emoji"],
                                           "total_before": 0, "total_after": 0, "gain": 0}
                fund_summaries[fid]["total_before"] += amount
                fund_summaries[fid]["total_after"] += new_amount
                fund_summaries[fid]["gain"] += gain

        channel = self._ann_channel()
        if channel and fund_summaries:
            await channel.send(embed=_fund_embed(list(fund_summaries.values()), today_is_crash_day))

    @tasks.loop(hours=24 * 7)
    async def tax_drain(self):
        await self.bot.wait_until_ready()
        async with db.pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, quid FROM economy WHERE quid > $1", WEALTH_TAX_THRESHOLD)
            for row in rows:
                tax = int((row["quid"] - WEALTH_TAX_THRESHOLD) * WEALTH_TAX_RATE)
                if tax > 0:
                    await conn.execute("UPDATE economy SET quid=quid-$1 WHERE user_id=$2", tax, row["user_id"])
                    await conn.execute(
                        "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'tax',$2,'weekly wealth tax')",
                        row["user_id"], tax
                    )

    @commands.command(name="loan",
                      help="take out a loan", usage="!loan <amount>")
    async def loan(self, ctx, amount: int):
        if amount < LOAN_MIN:
            return await ctx.send(f"minimum loan is **{LOAN_MIN}** {QUID_EMOJI}.")
        async with db.pool.acquire() as conn:
            await ensure_bank(conn, ctx.author.id)
            row = await get_bank_row(conn, ctx.author.id)
            wallet = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0
            if row["loan_amount"] > 0:
                return await ctx.send(f"you already have an outstanding loan of **{row['loan_amount']}** {QUID_EMOJI}.")
            max_loan = min(wallet * MAX_LOAN_MULTIPLIER, MAX_LOAN_HARD_CAP)
            if amount > max_loan:
                return await ctx.send(
                    f"you can borrow at most **{int(max_loan)}** {QUID_EMOJI} "
                    f"(2x your wallet, capped at {MAX_LOAN_HARD_CAP:,})."
                )
        embed = discord.Embed(
            title="💳 loan confirmation",
            description=(
                f"**amount:** {amount} {QUID_EMOJI}\n"
                f"**interest:** {INTEREST_RATE_LOAN*100:.0f}% per day\n\n"
                "⚠️ interest compounds daily."
            ),
            color=discord.Color.orange()
        )
        view = ConfirmView(ctx.author.id)
        msg  = await ctx.send(embed=embed, view=view)
        await view.wait()
        if not view.confirmed:
            return
        async with db.pool.acquire() as conn:
            await conn.execute("UPDATE finance_bank SET loan_amount=$1, loan_taken_at=NOW() WHERE user_id=$2", amount, ctx.author.id)
            await conn.execute("UPDATE economy SET quid=quid+$1 WHERE user_id=$2", amount, ctx.author.id)
            await conn.execute(
                "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'loan_taken',$2,'loan taken')",
                ctx.author.id, amount
            )
        await msg.edit(content=f"💳 loan of **{amount}** {QUID_EMOJI} approved.", embed=None, view=None)
        await _fire(self.bot, ctx.author, "finance.first_loan")
        await _progress(self.bot, ctx.author, "finance.loans_taken")

    @commands.command(name="repay",
                      help="repay your loan", usage="!repay <amount|all>")
    async def repay(self, ctx, amount: str):
        async with db.pool.acquire() as conn:
            await ensure_bank(conn, ctx.author.id)
            row = await get_bank_row(conn, ctx.author.id)
            wallet = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0
            if not row or row["loan_amount"] <= 0:
                return await ctx.send("you have no outstanding loan.")
            owed = row["loan_amount"]
            amt = owed if amount.lower() == "all" else int(amount)
            if amt <= 0:
                return await ctx.send("amount must be positive.")
            if amt > wallet:
                return await ctx.send(f"you only have **{wallet}** {QUID_EMOJI}.")
            actual_pay  = min(amt, owed)
            await conn.execute("UPDATE economy SET quid=quid-$1 WHERE user_id=$2", actual_pay, ctx.author.id)
            remaining = owed - actual_pay
            if remaining <= 0:
                await conn.execute("UPDATE finance_bank SET loan_amount=0, loan_taken_at=NULL WHERE user_id=$1", ctx.author.id)
            else:
                await conn.execute("UPDATE finance_bank SET loan_amount=loan_amount-$1 WHERE user_id=$2", actual_pay, ctx.author.id)
            await conn.execute(
                "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'loan_repaid',$2,'loan repayment')",
                ctx.author.id, actual_pay
            )
        if remaining <= 0:
            await ctx.send("✅ loan fully repaid! you're debt-free.")
            await _fire(self.bot, ctx.author, "finance.loan_repaid")
        else:
            await ctx.send(f"💳 paid **{actual_pay}** {QUID_EMOJI}. remaining: **{remaining}** {QUID_EMOJI}.")

 
    @commands.command(name="cd",
                      help="open a cd or claim it when ready",
                      usage="!cd [amount]")
    async def certificate_of_deposit(self, ctx, amount: int = None):
        async with db.pool.acquire() as conn:
            await ensure_bank(conn, ctx.author.id)
            row = await get_bank_row(conn, ctx.author.id)
 
            if row and row["cd_amount"] > 0:
                now = datetime.datetime.now(datetime.timezone.utc)
                matures = row["cd_matures_at"]
                if matures.tzinfo is None:
                    matures = matures.replace(tzinfo=datetime.timezone.utc)
                if now < matures:
                    ts = int(matures.timestamp())
                    return await ctx.send(f"📀 your cd isn't ready yet. claim it <t:{ts}:R>.")
                payout = int(row["cd_amount"] * (1 + CD_MULTIPLIER))
                profit = payout - row["cd_amount"]
                await conn.execute("UPDATE economy SET quid=quid+$1 WHERE user_id=$2", payout, ctx.author.id)
                await conn.execute("UPDATE finance_bank SET cd_amount=0, cd_matures_at=NULL WHERE user_id=$1", ctx.author.id)
                await conn.execute(
                    "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'cd_claim',$2,'CD matured')",
                    ctx.author.id, payout
                )
                await ctx.send(f"📀 cd matured! **{payout}** {QUID_EMOJI} (+**{profit}** {QUID_EMOJI} profit).")
                await _fire(self.bot, ctx.author, "finance.cd_claimed")
                await _progress(self.bot, ctx.author, "finance.cd_claimed_count")
                return
 
            if amount is None:
                return await ctx.send("you have no active cd. use `!cd <amount>` to open one.")
            if amount < 100:
                return await ctx.send(f"minimum cd is **100** {QUID_EMOJI}.")
            wallet = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0
            if amount > wallet:
                return await ctx.send(f"you only have **{wallet}** {QUID_EMOJI}.")
            matures_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=CD_TERM_HOURS)
            await conn.execute("UPDATE economy SET quid=quid-$1 WHERE user_id=$2", amount, ctx.author.id)
            await conn.execute(
                "UPDATE finance_bank SET cd_amount=$1, cd_matures_at=$2 WHERE user_id=$3",
                amount, matures_at, ctx.author.id
            )
 
        payout = int(amount * (1 + CD_MULTIPLIER))
        ts = int(matures_at.timestamp())
        await ctx.send(
            f"📀 cd opened! **{amount}** {QUID_EMOJI} locked for 24h.\n"
            f"receive **{payout}** {QUID_EMOJI} when ready. run `!cd` to claim <t:{ts}:R>."
        )
        await _fire(self.bot, ctx.author, "finance.first_cd")

    @commands.command(name="market",
                      help="view current stock prices", usage="!market", aliases=["stocks", "stock"])
    async def market(self, ctx):
        prices = {}
        async with db.pool.acquire() as conn:
            for ticker in STOCKS:
                p = await conn.fetchval("SELECT price FROM finance_stock_prices WHERE ticker=$1", ticker)
                prices[ticker] = p or STOCKS[ticker]["price"]
        view = StockMarketView(self.bot, prices)
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="buy",
                      help="buy stock shares", usage="!buy <TICKER> <shares>")
    async def buy_stock(self, ctx, ticker: str, shares: int):
        ticker = ticker.upper()
        if ticker not in STOCKS:
            return await ctx.send(f"unknown ticker **{ticker}**. use `!market`.")
        if shares <= 0:
            return await ctx.send("must buy at least 1 share.")
        async with db.pool.acquire() as conn:
            price  = await conn.fetchval("SELECT price FROM finance_stock_prices WHERE ticker=$1", ticker) or STOCKS[ticker]["price"]
            cost   = price * shares
            wallet = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0
            if cost > wallet:
                return await ctx.send(f"need **{cost}** {QUID_EMOJI} but only have **{wallet}**.")
            portfolio   = await get_portfolio(conn, ctx.author.id)
            tickers_held = [r["ticker"] for r in portfolio]
            if ticker not in tickers_held and len(tickers_held) >= PORTFOLIO_MAX_STOCKS:
                return await ctx.send(f"portfolio full ({PORTFOLIO_MAX_STOCKS} stocks max).")
            stamp = max(1, int(cost * STAMP_DUTY_RATE))
            total_deduct = cost + stamp
            if total_deduct > wallet:
                return await ctx.send(
                    f"need **{cost}** {QUID_EMOJI} + **{stamp}** stamp duty = **{total_deduct}** total, "
                    f"but only have **{wallet}**."
                )
            await conn.execute("UPDATE economy SET quid=quid-$1 WHERE user_id=$2", total_deduct, ctx.author.id)
            await conn.execute(
                """
                INSERT INTO finance_portfolio (user_id, ticker, shares, avg_cost, bought_at)
                VALUES ($1,$2,$3,$4,NOW())
                ON CONFLICT (user_id, ticker) DO UPDATE
                SET shares   = finance_portfolio.shares + $3,
                    avg_cost = (finance_portfolio.avg_cost * finance_portfolio.shares + $4 * $3)
                               / (finance_portfolio.shares + $3),
                    bought_at = NOW()
                """,
                ctx.author.id, ticker, shares, price
            )
            await conn.execute(
                "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'buy_stock',$2,$3)",
                ctx.author.id, cost, f"bought {shares}x {ticker} @ {price}"
            )
            if stamp > 0:
                await conn.execute(
                    "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'tax',$2,'stamp duty on buy')",
                    ctx.author.id, stamp
                )
        info = STOCKS[ticker]
        await ctx.send(
            f"{info['emoji']} bought **{shares}x {ticker}** for **{cost}** {QUID_EMOJI} ({price} each).\n"
            f"🏛️ stamp duty: **{stamp}** {QUID_EMOJI}  *(1.5% transaction tax)*"
        )
        await _fire(self.bot, ctx.author, "finance.first_stock")
        await _progress(self.bot, ctx.author, "finance.stocks_bought", shares)

    @commands.command(name="sellstock",
                      help="sell stock shares", usage="!sellstock <TICKER> <shares|all>")
    async def sell_stock(self, ctx, ticker: str, shares: str):
        ticker = ticker.upper()
        if ticker not in STOCKS:
            return await ctx.send(f"unknown ticker **{ticker}**.")
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT shares, avg_cost, bought_at FROM finance_portfolio WHERE user_id=$1 AND ticker=$2",
                ctx.author.id, ticker
            )
            if not row or row["shares"] <= 0:
                return await ctx.send(f"you don't own any **{ticker}** shares.")
            amt = row["shares"] if shares.lower() == "all" else int(shares)
            if amt > row["shares"]:
                return await ctx.send(f"you only own {row['shares']} shares.")
            price   = await conn.fetchval("SELECT price FROM finance_stock_prices WHERE ticker=$1", ticker) or STOCKS[ticker]["price"]
            revenue = price * amt
            profit  = revenue - (row["avg_cost"] * amt)

            held_seconds = None
            if row["bought_at"]:
                bt = row["bought_at"]
                if bt.tzinfo is None:
                    bt = bt.replace(tzinfo=datetime.timezone.utc)
                held_seconds = (datetime.datetime.now(datetime.timezone.utc) - bt).total_seconds()
            tax      = _tax_on_profit(int(profit), held_seconds)
            net_gain = int(profit) - tax

            await conn.execute("UPDATE economy SET quid=quid+$1 WHERE user_id=$2", revenue - tax, ctx.author.id)
            if row["shares"] - amt <= 0:
                await conn.execute("DELETE FROM finance_portfolio WHERE user_id=$1 AND ticker=$2", ctx.author.id, ticker)
            else:
                await conn.execute("UPDATE finance_portfolio SET shares=$1 WHERE user_id=$2 AND ticker=$3",
                                   row["shares"] - amt, ctx.author.id, ticker)
            await conn.execute(
                "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'sell_stock',$2,$3)",
                ctx.author.id, revenue, f"sold {amt}x {ticker} @ {price}"
            )
            if tax > 0:
                await conn.execute(
                    "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'tax',$2,$3)",
                    ctx.author.id, tax, f"cap-gains tax on {ticker} sale"
                )

        info   = STOCKS[ticker]
        color  = discord.Color.green() if net_gain >= 0 else discord.Color.red()
        sign   = "+" if net_gain >= 0 else ""
        embed  = discord.Embed(
            title=f"{info['emoji']} sold {amt}x {ticker}",
            description=(
                f"**revenue:** {revenue} {QUID_EMOJI}\n"
                f"**profit:** {'+' if profit>=0 else ''}{int(profit)} {QUID_EMOJI}\n"
                f"**tax:** -{tax} {QUID_EMOJI}"
                + (f"  _(30% short-term)_" if held_seconds and held_seconds < 86400 else "") +
                f"\n**net:** {sign}{net_gain} {QUID_EMOJI}"
            ),
            color=color
        )
        await ctx.send(embed=embed)
        if profit > 0:
            await _fire(self.bot, ctx.author, "finance.stock_profit")
            await _progress(self.bot, ctx.author, "finance.total_profit", int(profit))
        if profit < 0:
            await _fire(self.bot, ctx.author, "finance.stock_loss")

    @commands.command(name="portfolio", aliases=["pf"],
                      help="view your stock portfolio", usage="!portfolio [@user]")
    async def portfolio(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        async with db.pool.acquire() as conn:
            rows = await get_portfolio(conn, target.id)
        prices = {}
        for r in rows:
            async with db.pool.acquire() as conn:
                p = await conn.fetchval("SELECT price FROM finance_stock_prices WHERE ticker=$1", r["ticker"])
                prices[r["ticker"]] = p or STOCKS.get(r["ticker"], {}).get("price", 0)
        view = PortfolioView(self.bot, target, rows, prices)
        await ctx.send(embed=view.build_embed())

    @commands.command(name="funds",
                      help="view available index funds", usage="!funds")
    async def funds(self, ctx):
        embed = discord.Embed(title="📈 index funds", color=discord.Color.teal())
        embed.description = "auto-compound daily. use `!invest <FUND> <amount>` / `!divest <FUND>`."
        for fid, fund in INDEX_FUNDS.items():
            embed.add_field(
                name=f"{fund['emoji']} **{fid}** - {fund['name']}",
                value=f"{fund['description']}\nmin: {fund['min_invest']} {QUID_EMOJI}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="invest",
                      help="invest in an index fund", usage="!invest <FUND> <amount>")
    async def invest(self, ctx, fund_id: str, amount: int):
        fund_id = fund_id.upper()
        fund    = INDEX_FUNDS.get(fund_id)
        if not fund:
            return await ctx.send(f"unknown fund **{fund_id}**. use `!funds`.")
        if amount < fund["min_invest"]:
            return await ctx.send(f"minimum is **{fund['min_invest']}** {QUID_EMOJI}.")
        async with db.pool.acquire() as conn:
            wallet = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0
            if amount > wallet:
                return await ctx.send(f"you need **{amount}** {QUID_EMOJI} but only have **{wallet}**.")
            existing = await conn.fetchval(
                "SELECT amount FROM finance_index_investments WHERE user_id=$1 AND fund=$2",
                ctx.author.id, fund_id
            )
            await conn.execute("UPDATE economy SET quid=quid-$1 WHERE user_id=$2", amount, ctx.author.id)
            if existing:
                await conn.execute(
                    "UPDATE finance_index_investments SET amount=amount+$1 WHERE user_id=$2 AND fund=$3",
                    amount, ctx.author.id, fund_id
                )
            else:
                await conn.execute(
                    "INSERT INTO finance_index_investments (user_id, fund, amount, invested_at) VALUES ($1,$2,$3,NOW())",
                    ctx.author.id, fund_id, amount
                )
            await conn.execute(
                "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'invest',$2,$3)",
                ctx.author.id, amount, f"invested in {fund_id}"
            )
        await ctx.send(f"{fund['emoji']} invested **{amount}** {QUID_EMOJI} in **{fund['name']}**.")
        await _fire(self.bot, ctx.author, "finance.first_investment")
        await _progress(self.bot, ctx.author, "finance.total_invested", amount)

    @commands.command(name="divest",
                      help="pull out of an index fund", usage="!divest <FUND>")
    async def divest(self, ctx, fund_id: str):
        fund_id = fund_id.upper()
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT amount FROM finance_index_investments WHERE user_id=$1 AND fund=$2",
                ctx.author.id, fund_id
            )
            if not row or row["amount"] <= 0:
                return await ctx.send(f"you have no investment in **{fund_id}**.")
            amount = row["amount"]
            await conn.execute("UPDATE economy SET quid=quid+$1 WHERE user_id=$2", amount, ctx.author.id)
            await conn.execute("DELETE FROM finance_index_investments WHERE user_id=$1 AND fund=$2", ctx.author.id, fund_id)
            await conn.execute(
                "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'divest',$2,$3)",
                ctx.author.id, amount, f"divested from {fund_id}"
            )
        await ctx.send(f"💰 withdrew **{amount}** {QUID_EMOJI} from **{fund_id}**.")

    @commands.command(name="marginbuy",
                      help="buy stocks on margin (2x leverage, 3% daily interest)",
                      usage="!marginbuy <TICKER> <shares>")
    async def margin_buy(self, ctx, ticker: str, shares: int):
        ticker = ticker.upper()
        if ticker not in STOCKS:
            return await ctx.send(f"unknown ticker **{ticker}**.")
        if shares <= 0:
            return await ctx.send("must buy at least 1 share.")
        async with db.pool.acquire() as conn:
            price      = await conn.fetchval("SELECT price FROM finance_stock_prices WHERE ticker=$1", ticker) or STOCKS[ticker]["price"]
            total_cost = price * shares
            wallet     = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0
            collateral = total_cost // int(MARGIN_MULTIPLIER)
            if collateral > wallet:
                return await ctx.send(
                    f"you need at least **{collateral}** {QUID_EMOJI} as collateral "
                    f"(half of **{total_cost}**), but you only have **{wallet}**."
                )
            margin_used = total_cost - collateral
            await conn.execute("UPDATE economy SET quid=quid-$1 WHERE user_id=$2", collateral, ctx.author.id)
            await conn.execute(
                """
                INSERT INTO finance_portfolio (user_id, ticker, shares, avg_cost, bought_at)
                VALUES ($1,$2,$3,$4,NOW())
                ON CONFLICT (user_id, ticker) DO UPDATE
                SET shares   = finance_portfolio.shares + $3,
                    avg_cost = (finance_portfolio.avg_cost * finance_portfolio.shares + $4 * $3)
                               / (finance_portfolio.shares + $3),
                    bought_at = NOW()
                """,
                ctx.author.id, ticker, shares, price
            )
            await conn.execute(
                """
                INSERT INTO finance_margin (user_id, margin_used)
                VALUES ($1,$2)
                ON CONFLICT (user_id) DO UPDATE SET margin_used=finance_margin.margin_used+$2
                """,
                ctx.author.id, margin_used
            )
            await conn.execute(
                "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'margin_buy',$2,$3)",
                ctx.author.id, total_cost, f"margin bought {shares}x {ticker} @ {price}"
            )
        await ctx.send(
            f"⚡ margin buy: **{shares}x {ticker}** for **{total_cost}** {QUID_EMOJI}\n"
            f"collateral: **{collateral}** {QUID_EMOJI}  |  borrowed: **{margin_used}** {QUID_EMOJI}\n"
            f"⚠️ {MARGIN_INTEREST_DAY*100:.0f}% daily interest on the borrowed amount. repay by selling with `!sellstock`."
        )

    @commands.command(name="transfer", aliases=["pay", "send"],
                      help="send quid to another user", usage="!transfer <@user> <amount>")
    async def transfer(self, ctx, member: discord.Member, amount: int):
        if member.id == ctx.author.id:
            return await ctx.send("you can't pay yourself.")
        if amount <= 0:
            return await ctx.send("amount must be positive.")
        async with db.pool.acquire() as conn:
            wallet = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0
            if amount > wallet:
                return await ctx.send(f"you only have **{wallet}** {QUID_EMOJI}.")
        view = ConfirmView(ctx.author.id)
        msg  = await ctx.send(f"send **{amount}** {QUID_EMOJI} to {member.mention}?", view=view)
        await view.wait()
        if not view.confirmed:
            return
        async with db.pool.acquire() as conn:
            wallet = await conn.fetchval("SELECT quid FROM economy WHERE user_id=$1", ctx.author.id) or 0
            if amount > wallet:
                return await msg.edit(content="you no longer have enough quid.", view=None)
            await conn.execute("UPDATE economy SET quid=quid-$1 WHERE user_id=$2", amount, ctx.author.id)
            await conn.execute(
                "INSERT INTO economy (user_id, quid) VALUES ($1,$2) ON CONFLICT (user_id) DO UPDATE SET quid=economy.quid+$2",
                member.id, amount
            )
            for uid, note in [(ctx.author.id, f"sent to {member.id}"), (member.id, f"received from {ctx.author.id}")]:
                await conn.execute(
                    "INSERT INTO finance_transactions (user_id, type, amount, note) VALUES ($1,'transfer',$2,$3)",
                    uid, amount, note
                )
        await msg.edit(content=f"✅ sent **{amount}** {QUID_EMOJI} to {member.mention}.", view=None)
        await _fire(self.bot, ctx.author, "finance.first_transfer")
        await _progress(self.bot, ctx.author, "finance.transfers_made")

    @commands.command(name="ledger",
                      help="view your recent transactions", usage="!ledger")
    async def ledger(self, ctx):
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT type, amount, note, created_at FROM finance_transactions "
                "WHERE user_id=$1 ORDER BY created_at DESC LIMIT 15",
                ctx.author.id
            )
        if not rows:
            return await ctx.send("no transactions yet.")
        embed = discord.Embed(title="📒 recent transactions", color=discord.Color.greyple())
        for row in rows:
            ts = int(row["created_at"].timestamp())
            embed.add_field(
                name=f"`{row['type']}` - {row['amount']} {QUID_EMOJI}",
                value=f"{row['note']}  •  <t:{ts}:R>",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="taxinfo",
                      help="view current tax brackets and rules", usage="!taxinfo")
    async def taxinfo(self, ctx):
        embed = discord.Embed(
            title="📋 tax information",
            color=discord.Color.dark_gold(),
            description=(
                "all capital gains (stocks) are taxed at sale time.\n"
                "losses are **not** refunded. losses reduce future tax brackets."
            )
        )
        embed.add_field(
            name="⚡ short-term (held < 24h)",
            value=f"**{int(SHORT_TERM_TAX_RATE*100)}%** flat rate on profit",
            inline=False
        )
        prev = 0
        for threshold, rate in TAX_BRACKETS:
            if threshold == float("inf"):
                embed.add_field(name=f"📊 long-term > {prev:,} {QUID_EMOJI} profit",
                                value=f"**{int(rate*100)}%**", inline=True)
            else:
                embed.add_field(name=f"📊 long-term {prev:,}–{threshold:,} {QUID_EMOJI} profit",
                                value=f"**{int(rate*100)}%**", inline=True)
            prev = threshold
        embed.add_field(
            name="🏛️ weekly wealth tax",
            value=f"{int(WEALTH_TAX_RATE*100)}% per week on wallet balance **above** {WEALTH_TAX_THRESHOLD:,} {QUID_EMOJI}",
            inline=False
        )
        embed.add_field(
            name="🪙 stamp duty",
            value=f"{int(STAMP_DUTY_RATE*100)}% on every stock purchase (added to buy cost)",
            inline=False
        )
        embed.add_field(
            name="⚡ margin interest",
            value=f"{int(MARGIN_INTEREST_DAY*100)}% daily on borrowed margin",
            inline=True
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FinanceCommands(bot))