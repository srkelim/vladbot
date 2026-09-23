from discord.ext import commands
import discord
import os
import time
import platform

AIRole = int(os.getenv("AIRole"))

CATEGORY_COGS = {
    "bot": ["BotCommands"],
    "economy": ["EconomyCommands"],
    "finance": ["FinanceCommands"],
    "fishing": ["FishingCog"],
    "fun": ["FunCommands", "AchievementCommands"],
    "gambling": ["GamblingCommands"],
    "games": ["Wordle"],
    "hell": ["HellCommands"],
    "music": ["MusicCommands"],
    "pet": ["PetCommands"],
    "quick": ["QuickCommands"],
    "social": ["SocialCommands"],
    "xp": ["XpCommand"],
}

ADMIN_ONLY_COMMANDS = [
    "addxp",
    "addquickcommand",
    "removequickcommand",
    "singadd",
    "singremove",
    "addquid",
    "giveach",
    "removeach",
    "eval",
    "setup_parthenon"
]

CATEGORY_EMOJIS = {
    "bot": "🤖",
    "economy": "💰",
    "finance": "📈",
    "fishing": "🐟",
    "fun": "🎉",
    "gambling": "🎲",
    "games": "🎮",
    "hell": "🔥",
    "music": "🎵",
    "pet": "🦉",
    "quick": "⚡",
    "social": "👥",
    "xp": "📈",
}

COMMANDS_PER_PAGE = 20

def _get_category_lines(bot, category: str, is_admin: bool) -> list[str]:
    lines = []
    for cog_name in CATEGORY_COGS.get(category, []):
        cog_obj = bot.get_cog(cog_name)
        if cog_obj is None:
            continue
        for cmd in cog_obj.get_commands():
            if cmd.hidden:
                continue
            if cmd.name in ADMIN_ONLY_COMMANDS and not is_admin:
                continue
            lines.append(f"`!{cmd.name}` - {cmd.help or 'no description'}")
    return lines


def _build_pages(bot, category: str, is_admin: bool) -> list[discord.Embed]:
    lines = _get_category_lines(bot, category, is_admin)
    emoji = CATEGORY_EMOJIS.get(category, "")

    if not lines:
        embed = discord.Embed(
            title=f"{emoji} {category}",
            description="*no commands in this category*",
            color=discord.Color.purple()
        )
        return [embed]

    chunks = [lines[i:i + COMMANDS_PER_PAGE] for i in range(0, len(lines), COMMANDS_PER_PAGE)]
    total  = len(chunks)
    pages  = []
    for i, chunk in enumerate(chunks):
        embed = discord.Embed(
            title=f"{emoji} {category}",
            description="\n".join(chunk),
            color=discord.Color.purple()
        )
        if total > 1:
            embed.set_footer(text=f"page {i + 1}/{total}")
        pages.append(embed)
    return pages


class PagerView(discord.ui.View):
    def __init__(self, *, pages: list[discord.Embed], author_id: int, parent_view: discord.ui.View):
        super().__init__(timeout=120)
        self.pages       = pages
        self.author_id   = author_id
        self.parent_view = parent_view
        self.page        = 0
        self._update_buttons()

    def _update_buttons(self):
        self.back_btn.disabled = False
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page == len(self.pages) - 1

    @discord.ui.button(label="‹‹ menu", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("not your menu", ephemeral=True)
        main_embed = discord.Embed(
            title="📖 command help",
            description="use the dropdown below to browse command categories\n\n🔒 some commands are admin-only",
            color=discord.Color.dark_purple()
        )
        await interaction.response.edit_message(embed=main_embed, view=self.parent_view)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("not your menu", ephemeral=True)
        self.page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.page], view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("not your menu", ephemeral=True)
        self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.page], view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class HelpSelect(discord.ui.Select):
    def __init__(self, *, bot, ctx, is_admin):
        self.bot      = bot
        self.ctx      = ctx
        self.is_admin = is_admin

        options = [
            discord.SelectOption(label=cat, value=cat, emoji=CATEGORY_EMOJIS.get(cat))
            for cat in CATEGORY_COGS.keys()
        ]
        super().__init__(placeholder="choose a category…", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("this menu ain't for you lil bro", ephemeral=True)

        category = self.values[0]
        pages    = _build_pages(self.bot, category, self.is_admin)

        if len(pages) == 1:
            await interaction.response.edit_message(embed=pages[0], view=self.view)
        else:
            pager = PagerView(pages=pages, author_id=self.ctx.author.id, parent_view=self.view)
            await interaction.response.edit_message(embed=pages[0], view=pager)

class HelpView(discord.ui.View):
    def __init__(self, *, bot, ctx, is_admin):
        super().__init__(timeout=120)
        self.add_item(HelpSelect(bot=bot, ctx=ctx, is_admin=is_admin))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", help="see the commands", usage="!help")
    async def help(self, ctx: commands.Context):
        is_admin = ctx.author.get_role(AIRole) is not None
        embed = discord.Embed(
            title="📖 command help",
            description="use the dropdown below to browse command categories\n\n🔒 some commands are admin-only",
            color=discord.Color.dark_purple()
        )
        await ctx.send(embed=embed, view=HelpView(bot=self.bot, ctx=ctx, is_admin=is_admin))

    @commands.command(name="info", help="learn more about the bot", usage="!info")
    async def status(self, ctx: commands.Context):
        uptime_seconds = int(time.time() - self.bot.start_time)
        uptime = time.strftime('%Hh %Mm %Ss', time.gmtime(uptime_seconds))
        ping   = round(self.bot.latency * 1000)

        status_embed = discord.Embed(color=discord.Color.purple())
        status_embed.set_thumbnail(url=self.bot.user.avatar)
        status_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        status_embed.add_field(name="discord.py version", value=f"`{discord.__version__}`")
        status_embed.add_field(name="python version", value=f"`{platform.python_version()}`", inline=True)
        status_embed.add_field(name='\u200b', value='\u200b')
        status_embed.add_field(name="🕒 uptime", value=f"{uptime}")
        status_embed.add_field(name="🏓 ping", value=f"{ping}ms", inline=True)
        await ctx.send(embed=status_embed)

async def setup(bot):
    await bot.add_cog(BotCommands(bot))