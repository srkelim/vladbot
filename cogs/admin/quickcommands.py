import os
import discord
import asyncio
from discord.ext import commands

from db import db

AIRole = int(os.getenv("AIRole"))

class QuickCommandsView(discord.ui.View):
    def __init__(self, ctx, commands_info, page_size=5):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.commands_info = commands_info
        self.page_size = page_size
        self.page = 0
        self.total_pages = (len(commands_info) + page_size - 1) // page_size

    def generate_embed(self):
        embed = discord.Embed(
            title="⚡ quick commands",
            description=f"page {self.page + 1}/{self.total_pages}",
            color=discord.Color.blue(),
        )

        start = self.page * self.page_size
        end = min(start + self.page_size, len(self.commands_info))

        for row in self.commands_info[start:end]:
            embed.add_field(
                name=row["command_name"],
                value=row["command_respond"],
                inline=False,
            )

        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

class QuickCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="removequickcommand",
        aliases=["rqc"],
        help="remove quick command",
        usage="!rqc command",
    )
    @commands.has_role(AIRole)
    async def deletequickcommand(self, ctx: commands.Context, command_name):
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    DELETE FROM quick_commands
                    WHERE command_name = $1
                    RETURNING command_name
                    """,
                    command_name.lower()
                )

            if not result:
                await ctx.send(f"`{command_name}` is not a quick command idiot")
            else:
                await ctx.send(f"`{command_name}` got deleted haha")

        except Exception as e:
            await ctx.send("random ahh error")
            print(f"Error deleting command: {e}")

    @commands.command(
        name="newquickcommand",
        aliases=["nqc"],
        help="add quick command",
        usage="!nqc commandname response",
    )
    @commands.has_role(AIRole)
    async def newquickcommand(self, ctx: commands.Context, command_name, *response):
        if not command_name:
            return await ctx.reply("blub wheres the command name")

        command_response = " ".join(response)
        if not command_response:
            return await ctx.reply("blub wheres the command response")

        try:
            async with db.pool.acquire() as conn:
                exists = await conn.fetchval(
                    """
                    SELECT 1 FROM quick_commands
                    WHERE command_name = $1
                    """,
                    command_name.lower()
                )

                if exists:
                    await ctx.reply("blub theres already a quick command with that name")
                    return

                await conn.execute(
                    """
                    INSERT INTO quick_commands (command_name, command_respond)
                    VALUES ($1, $2)
                    """,
                    command_name.lower(),
                    command_response
                )

            await ctx.reply(f"`{command_name}` got created yay")

        except Exception as e:
            await ctx.send("random ahh error")
            print(f"Error adding command: {e}")

    @commands.command(
        name="quickcommandslist",
        aliases=["qcl"],
        help="see all quick commands",
        usage="!qcl",
    )
    async def getquickcommands(self, ctx: commands.Context):
        async with db.pool.acquire() as conn:
            commands_info = await conn.fetch(
                """
                SELECT command_name, command_respond
                FROM quick_commands
                ORDER BY command_name
                """
            )

        if not commands_info:
            return await ctx.reply("there are no quick commands")

        view = QuickCommandsView(ctx, commands_info)
        message = await ctx.send(embed=view.generate_embed(), view=view)
        view.message = message

async def setup(bot):
    await bot.add_cog(QuickCommands(bot))
