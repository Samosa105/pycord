import discord
import os
os.system("pip install -U py-cord --pre")

bot = discord.Bot()

@bot.event
async def on_ready():
  print("Bot has been t u r n e d on ( ͡° ͜ʖ ͡°)")
  await bot.change_presence(status=discord.Status.online, activity=discord.Game(name='Life')) #Bot status

@bot.slash_command(guild_ids=[972198985441902644])
async def hello(ctx):
    await ctx.respond("Hello!")

@bot.slash_command(
    name="confess", 
    guild_ids=[972198985441902644],
    description="Use to make a Confession"
) 
async def global_command(ctx, num: str):  # Takes one str parameter
    await ctx.respond(f"This is a global command, {num}!")

bot.run(os.getenv('TOKEN'))




