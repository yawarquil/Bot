"""
StreamVault Discord Welcome Bot
Sends embeds on member join/leave. Uses discord.py (needs Python <=3.12).
"""
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WELCOME_CH_ID = 1518949506656505876   # 👥-users
LEAVE_CH_ID = 1518949510687232073     # 🚪-members-left

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Welcome bot online as {bot.user.name}")


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CH_ID)
    if not channel:
        return

    count = len(member.guild.members)

    embed = discord.Embed(
        title="🎉 Welcome to StreamVault! 🎉",
        description=f"Hey {member.mention}, welcome to our community!\nWe are absolutely thrilled to have you here.",
        color=discord.Color.from_rgb(114, 137, 218),
    )

    if member.display_avatar:
        embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(
        name="📜 Quick Reminder",
        value="Check <#1518948909513310281> for rules and <#1518948915087544340> to pick your interests!",
        inline=False,
    )
    embed.set_footer(text=f"You are our {count}th member! • Enjoy your stay ✨")

    await channel.send(embed=embed)


@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LEAVE_CH_ID)
    if not channel:
        return

    remaining = len(member.guild.members)

    embed = discord.Embed(
        title="👋 Goodbye!",
        description=f"**{member.name}** just left the server.\nWe're sad to see you go!",
        color=discord.Color.red(),
    )

    if member.display_avatar:
        embed.set_thumbnail(url=member.display_avatar.url)

    embed.set_footer(text=f"We now have {remaining} members remaining.")
    await channel.send(embed=embed)


@bot.command()
async def testjoin(ctx):
    await on_member_join(ctx.author)


@bot.command()
async def testleave(ctx):
    await on_member_remove(ctx.author)


if __name__ == "__main__":
    if not TOKEN:
        print("DISCORD_BOT_TOKEN not set!")
    else:
        bot.run(TOKEN)
