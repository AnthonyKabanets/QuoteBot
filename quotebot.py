import discord
from discord.ext import commands

import logging
import sqlite3
import datetime

import constants
import helpers
import quote

import adapter
adapter.registerAdapters()
adapter.registerConverters()

config = helpers.getConfigFile()
logging.basicConfig(level=logging.INFO)

botIntents = discord.Intents.default()
botIntents.message_content = True
botIntents.reactions = True
bot = commands.Bot(command_prefix=config["Prefix"], 
    intents = botIntents,
    activity=discord.Activity(type=discord.ActivityType.watching, name=config["Presence"]))
emoji = config['Emoji']


con = sqlite3.connect(config['Quotes'], autocommit=False)
bot.db_connection = con

helpers.initTable(con, 'quotes') #Make quotes table if it does not exist.
extensions = ["alias", "quote", "admin"]

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    for extension in extensions:
        await bot.load_extension(extension)

@bot.command(help = "Reload extensions.")
async def refreshCommands(ctx):
    for extension in extensions:
        await bot.reload_extension(extension)
    await ctx.send("Commands synced.")

bot.run(config["Token"], reconnect=True)
#end command lets the client know that it is a bot
#also if connection drops, bot will attempt to reconnect
#saves trouble of manually restarting in the event of connection loss
