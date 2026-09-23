import discord
from discord.ext import commands
import os
import yt_dlp
import traceback
import asyncio

AIRole = int(os.getenv("AIRole"))

SONGS_DIR = os.path.join(os.path.dirname(__file__), "songs")
os.makedirs(SONGS_DIR, exist_ok=True)

class SingListView(discord.ui.View):
    def __init__(self, ctx, tracks, items_per_page=10):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.tracks = tracks
        self.items_per_page = items_per_page
        self.page = 0
        self.total_pages = (len(tracks) + items_per_page - 1) // items_per_page
        self.message = None

    def generate_embed(self):
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        page_tracks = self.tracks[start:end]

        track_list = [
            f"**{t[0]}** - `{t[1]}`"
            for t in page_tracks
        ]

        embed = discord.Embed(
            title="🎵 track list",
            description="\n".join(track_list),
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"page {self.page + 1}/{self.total_pages}")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id

    @discord.ui.button(label="◀", style=discord.ButtonStyle.success)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(
                embed=self.generate_embed(),
                view=self
            )
        else:
            await interaction.response.defer()

    @discord.ui.button(label="▶", style=discord.ButtonStyle.success)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
            await interaction.response.edit_message(
                embed=self.generate_embed(),
                view=self
            )
        else:
            await interaction.response.defer()

    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_tracks(self):
        tracks = []
        for file in os.listdir(SONGS_DIR):
            if file.endswith(".mp3"):
                try:
                    number, name_ext = file.split("_", 1)
                    name = os.path.splitext(name_ext)[0]
                    tracks.append((int(number), name, os.path.join(SONGS_DIR, file)))
                except ValueError:
                    continue
        return sorted(tracks, key=lambda x: x[0])

    @commands.command(name="sing", help="sing song silksong", usage="!sing <track number>")
    async def sing(self, ctx: commands.Context, track_number: int):
        tracks = self.get_tracks()
        track = next((t for t in tracks if t[0] == track_number), None)

        if not track:
            return await ctx.send("invalid track, check `!singlist`")

        _, track_name, file_path = track

        if not ctx.author.voice:
            return await ctx.send("join a vc first")

        channel = ctx.author.voice.channel
        vc = ctx.voice_client

        if vc is None:
            try:
                vc = await channel.connect()
            except Exception as e:
                print("[VOICE CONNECT ERROR]", e)
                return await ctx.send("failed to connect to voice")
        elif vc.channel != channel:
            await vc.move_to(channel)

        if vc.is_playing():
            vc.stop()

        source = discord.FFmpegPCMAudio(file_path)
        vc.play(source)

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{track_name}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="requested by", value=ctx.author.mention)
        await ctx.send(embed=embed)

        def after_play(error):
            if error:
                print("Playback error:", error)

            async def leave_later():
                await asyncio.sleep(60)
                if vc.is_connected() and not vc.is_playing():
                    await vc.disconnect()

            asyncio.run_coroutine_threadsafe(leave_later(), self.bot.loop)

    @commands.command(name="singlist", help="list all of the tracks", usage="!singlist")
    async def singlist(self, ctx: commands.Context):
        tracks = self.get_tracks()

        if not tracks:
            return await ctx.send("there are no tracks :pensive:")

        view = SingListView(ctx, tracks, items_per_page=10)
        message = await ctx.send(
            embed=view.generate_embed(),
            view=view
        )
        view.message = message

    @commands.command(name="singadd", help="add and download a new song", usage="!singadd <name> <YouTube URL>")
    @commands.has_role(AIRole)
    async def singadd(self, ctx: commands.Context, name: str, url: str):
        tracks = self.get_tracks()
        next_number = tracks[-1][0] + 1 if tracks else 1

        filename = f"{next_number}_{name}"
        file_path = os.path.join(SONGS_DIR, filename)

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": file_path + ".%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        embed = discord.Embed(
            title="new song added",
            description=f"**{name}** has been added and downloaded",
            timestamp=ctx.message.created_at,
            color=discord.Color.green()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.add_field(name="Track Number", value=next_number, inline=True)
        embed.add_field(name="Added by", value=ctx.author.display_name, inline=True)
        embed.set_footer(text=ctx.guild.name if ctx.guild else "")

        await ctx.send(embed=embed)

    @commands.command(name="singremove", help="remove a song from the library", usage="!singremove <track number>")
    @commands.has_role(AIRole)
    async def singremove(self, ctx: commands.Context, track_number: int):
        tracks = self.get_tracks()
        track = next((t for t in tracks if t[0] == track_number), None)

        if not track:
            await ctx.send("NOT a VALID. TRACK. BRO.")
            return

        _, track_name, file_path = track

        os.remove(file_path)
        await ctx.send(f"removed track **{track_name}** successfully!!!!!")

        embed = discord.Embed(
            title="🗑️ Song Removed",
            description=f"**{track_name}** has been removed",
            timestamp=ctx.message.created_at,
            color=discord.Color.red()
        )
        embed.add_field(name="track number", value=track_number, inline=True)
        embed.add_field(name="removed by", value=ctx.author.display_name, inline=True)

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCommands(bot))