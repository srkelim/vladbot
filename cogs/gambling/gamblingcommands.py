import discord
from discord.ext import commands, tasks
import random
import asyncio
import datetime
from cogs.achievements import hooks

from config import LOTTERY_TICKET_PRICE, LOTTERY_DAYS, LOTTERY_CHANNEL_ID, LOTTERY_ROLE_ID, QUID_EMOJI, LOTTERY_ENABLED
from db import db

from cogs.economy.economycommands import (
    RED_NUMBERS,
    BLACK_NUMBERS,
    create_deck,
    hand_value,
    update_negative_state,
    next_lottery_draw_ts,
)

LOTTERY_TIME = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)

class BlackjackView(discord.ui.View):
    def __init__(self, ctx, deck, player_hand, dealer_hand, bet):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.deck = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.bet = bet

    async def interaction_check(self, interaction):
        return interaction.user.id == self.ctx.author.id

    async def resolve_stand(self, interaction, internal=False):
        while hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())

        player_total = hand_value(self.player_hand)
        dealer_total = hand_value(self.dealer_hand)

        async with db.pool.acquire() as conn:
            if dealer_total > 21 or player_total > dealer_total:
                await conn.execute(
                    "UPDATE economy SET quid = quid + $1 WHERE user_id = $2",
                    self.bet * 2, self.ctx.author.id
                )
                result = f"✅ you won **{self.bet}** {QUID_EMOJI}"
            elif player_total < dealer_total:
                result = f"❌ you lost **{self.bet}** {QUID_EMOJI}"
            else:
                await conn.execute(
                    "UPDATE economy SET quid = quid + $1 WHERE user_id = $2",
                    self.bet, self.ctx.author.id
                )
                result = "🤝 tie! bet returned"

        await update_negative_state(self.ctx.bot, self.ctx.author.id)

        content = f"{self.format_state(True)}\n{result}"

        await interaction.message.edit(content=content, view=None)

        self.stop()

    def format_state(self, reveal_dealer=False):
        player_total = hand_value(self.player_hand)
        dealer_display = (
            ", ".join(self.dealer_hand)
            if reveal_dealer else f"{self.dealer_hand[0]}, [hidden]"
        )
        dealer_total = hand_value(self.dealer_hand) if reveal_dealer else "?"
        return (
            f"🃏 **blackjack**\n"
            f"your hand: {', '.join(self.player_hand)} (total: {player_total})\n"
            f"dealer hand: {dealer_display} (total: {dealer_total})"
        )

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, _):
        self.player_hand.append(self.deck.pop())
        player_total = hand_value(self.player_hand)

        if player_total == 21:
            await self.resolve_stand(interaction)
            return

        if player_total > 21:
            await update_negative_state(self.ctx.bot, self.ctx.author.id)

            await interaction.response.edit_message(
                content=f"{self.format_state(True)}\n💥 you busted! lost **{self.bet}** {QUID_EMOJI}",
                view=None
            )
            self.stop()
            return

        await interaction.response.edit_message(
            content=self.format_state(),
            view=self
        )

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.success)
    async def stand(self, interaction: discord.Interaction, button):
        await self.resolve_stand(interaction)

class LotteryView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="buy ticket",
        style=discord.ButtonStyle.success,
        emoji="🎟️",
        custom_id="lottery_buy_ticket"
    )
    async def buy(self, interaction: discord.Interaction, _):
        guild = interaction.guild
        member = interaction.user
        role = guild.get_role(LOTTERY_ROLE_ID)

        if role in member.roles:
            return await interaction.response.send_message(
                "❌ you already bought a ticket",
                ephemeral=True
            )

        async with db.pool.acquire() as conn:
            balance = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1",
                member.id
            ) or 0

            if balance < LOTTERY_TICKET_PRICE:
                return await interaction.response.send_message(
                    "❌ you don't have enough quid",
                    ephemeral=True
                )

            await conn.execute(
                "UPDATE economy SET quid = quid - $1 WHERE user_id = $2",
                LOTTERY_TICKET_PRICE, member.id
            )

        await update_negative_state(self.bot, member.id)
        await member.add_roles(role)

        await interaction.response.send_message(
            f"✅ ticket purchased (-{LOTTERY_TICKET_PRICE} {QUID_EMOJI})",
            ephemeral=True
        )

class GamblingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(LotteryView(bot))

        if not self.lottery_task.is_running():
            self.lottery_task.start()

    @commands.command(name="lottery", help="buy a lottery ticket to see if yrou'e lucky", usage="!lottery")
    async def lottery(self, ctx):
        role = ctx.guild.get_role(LOTTERY_ROLE_ID)
        participants = len(role.members) if role else 0
        jackpot = participants * LOTTERY_TICKET_PRICE

        embed = discord.Embed(
            title="🎟️ lottery",
            description=(
                f"**ticket price:** {LOTTERY_TICKET_PRICE} {QUID_EMOJI}\n"
                f"**prize pool:** {jackpot} {QUID_EMOJI}\n"
                f"**ends:** <t:{next_lottery_draw_ts()}:R>"
            ),
            color=discord.Color.gold()
        )

        await ctx.send(embed=embed, view=LotteryView(self.bot))

    @commands.command(name="roulette", help="play roulette h", usage="!roulette <amount> <red/black/0-36>")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def roulette(self, ctx, amount: int, bet: str):
        if amount <= 0:
            return await ctx.send("bet must be greater than 0")

        async with db.pool.acquire() as conn:
            balance = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1",
                ctx.author.id
            ) or 0

            if balance < amount:
                return await ctx.send("you don't have enough quid")

            await conn.execute(
                "UPDATE economy SET quid = quid - $1 WHERE user_id = $2",
                amount, ctx.author.id
            )

        await update_negative_state(self.bot, ctx.author.id)

        bet = bet.lower()
        result = random.randint(0, 36)

        if result in RED_NUMBERS:
            color, emoji = "red", "🔴"
        elif result in BLACK_NUMBERS:
            color, emoji = "black", "⚫"
        else:
            color, emoji = "green", "🟢"

        async with db.pool.acquire() as conn:
            has_edge = await conn.fetchval(
                "SELECT house_edge FROM user_unlocks WHERE user_id=$1", ctx.author.id
            ) or False

        win = (
            bet == color or
            (bet.isdigit() and int(bet) == result)
        )

        if bet.isdigit():
            payout = amount * 36
        elif has_edge:
            payout = int(amount * 2.1)
        else:
            payout = amount * 2

        if win:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE economy SET quid = quid + $1 WHERE user_id = $2",
                    payout, ctx.author.id
                )
            await update_negative_state(self.bot, ctx.author.id)

        await ctx.send(
            f"🎰 landed on **{result} ({emoji})**\n"
            f"{'✅ won' if win else '❌ lost'} **{payout if win else amount}** {QUID_EMOJI}"
        )

    @commands.command(name="coinflip", aliases=["cf"], help="flip a coin", usage="!coinflip <amount> <heads/tails>")
    async def coinflip(self, ctx, amount: int, choice: str):
        if amount <= 0:
            return await ctx.send("bet must be > 0")

        choice = choice.lower()
        if choice not in ("heads", "tails"):
            return await ctx.send("choose heads or tails")

        async with db.pool.acquire() as conn:
            bal = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1",
                ctx.author.id
            ) or 0

            if bal < amount:
                return await ctx.send("not enough quid")

            await conn.execute(
                "UPDATE economy SET quid = quid - $1 WHERE user_id = $2",
                amount,
                ctx.author.id
            )

        async with db.pool.acquire() as conn:
            has_edge = await conn.fetchval(
                "SELECT house_edge FROM user_unlocks WHERE user_id=$1", ctx.author.id
            ) or False

        await update_negative_state(self.bot, ctx.author.id)

        msg = await ctx.send("flipping...")
        await asyncio.sleep(1)

        if has_edge:
            result = random.choices(("heads", "tails"), weights=(52, 48), k=1)[0]
        else:
            result = random.choice(("heads", "tails"))

        if result == choice:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE economy SET quid = quid + $1 WHERE user_id = $2",
                    amount * 2,
                    ctx.author.id
                )
            await update_negative_state(self.bot, ctx.author.id)

        await msg.edit(
            content=f"🪙 **{result}** - "
            f"{'won' if result == choice else 'lost'} {amount} {QUID_EMOJI}"
        )


    @commands.command(name="blackjack", aliases=["bj"], help="play jack black", usage="!blackjack <amount>")
    async def blackjack(self, ctx, amount: int):
        if amount <= 0:
            return await ctx.send("bet must be > 0")

        async with db.pool.acquire() as conn:
            bal = await conn.fetchval(
                "SELECT quid FROM economy WHERE user_id = $1",
                ctx.author.id
            ) or 0
            if bal < amount:
                return await ctx.send("not enough quid")

            # deduct upfront so the game can't be abandoned for free
            await conn.execute(
                "UPDATE economy SET quid = quid - $1 WHERE user_id = $2",
                amount, ctx.author.id
            )

        await update_negative_state(self.bot, ctx.author.id)

        deck = create_deck()
        random.shuffle(deck)

        view = BlackjackView(
            ctx,
            deck,
            [deck.pop(), deck.pop()],
            [deck.pop(), deck.pop()],
            amount
        )

        await ctx.send(view.format_state(), view=view)

    @tasks.loop(time=LOTTERY_TIME)
    async def lottery_task(self):
        await self.bot.wait_until_ready()

        if not LOTTERY_ENABLED:
            return
        if not LOTTERY_ROLE_ID or not LOTTERY_CHANNEL_ID:
            return

        today = datetime.date.today()
        if today.toordinal() % LOTTERY_DAYS != 0:
            return

        for guild in self.bot.guilds:
            role = guild.get_role(LOTTERY_ROLE_ID)
            channel = guild.get_channel(LOTTERY_CHANNEL_ID)

            if not role or not channel:
                continue

            participants = [m for m in role.members if not m.bot]
            if not participants:
                continue

            winner = random.choice(participants)
            jackpot = len(participants) * LOTTERY_TICKET_PRICE

            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE economy SET quid = quid + $1 WHERE user_id = $2",
                    jackpot,
                    winner.id
                )

            await update_negative_state(self.bot, winner.id)

            await channel.send(
                content=role.mention,
                embed=discord.Embed(
                    title="🎉 lottery winner!",
                    description=f"{winner.mention} won **{jackpot} {QUID_EMOJI}**",
                    color=discord.Color.gold()
                )
            )

            for member in participants:
                await member.remove_roles(role)

async def setup(bot: commands.Bot):
    await bot.add_cog(GamblingCommands(bot))