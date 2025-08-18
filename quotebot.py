import discord
from discord.ext import commands
from discord import app_commands

import logging
import sqlite3
import datetime

import constants
import helpers
import Printer

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
extensions = ["alias", "Printer", "admin"]

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    for extension in extensions:
        await bot.load_extension(extension)
    

@bot.command(help = "Prints how many times a person has been quoted.")
async def quotedCount(ctx, quoteAuthor):
    quoteAuthor = bot.get_cog("Alias").fetchAlias(quoteAuthor)[1]
    cur = con.cursor()
    cur.execute("SELECT COUNT() FROM quotes WHERE quoteAuthor = :name", {"name": quoteAuthor})
    quoteCount = cur.fetchone()[0]
    await ctx.channel.send(quoteAuthor + " has " + str(quoteCount) + " quotes.")
    #await ctx.message.add_reaction(emoji)

@bot.command(help = "Prints the top quoted people.", aliases=['quoteRank'])
async def rank(ctx, numquotes=5):
    cur = con.cursor()
    cur.execute("SELECT quoteAuthor, COUNT(quoteAuthor) FROM quotes GROUP BY quoteAuthor ORDER BY COUNT(quoteAuthor) DESC LIMIT :numQuotes", {"numQuotes": numquotes})
    rows = cur.fetchall()
    tempString = ""
    for row in rows:
        tempString += ("Name: " + str(row[0]) + "\n    Quotes: " + str(row[1]) + "\n")
    
    await ctx.send(tempString)

@bot.command(help = "Prints the number of times a user has added quotes.")
async def quoterCount(ctx, quoteRecorder):
    cur = con.cursor()
    cur.execute("SELECT COUNT() FROM quotes WHERE quoteRecorder = :name", {"name": quoteRecorder})
    quoteCount = cur.fetchone()[0]
    await ctx.channel.send(quoteRecorder + " has recorded " + str(quoteCount) + " quotes.")
    #await ctx.message.add_reaction(emoji)

@bot.command(help = "Prints the total number of quotes saved.")
async def totalQuotes(ctx):
    cur = con.cursor()
    cur.execute("SELECT COUNT() FROM quotes")
    quoteCount = cur.fetchone()[0]
    await ctx.channel.send(str(quoteCount) + " quotes recorded.")
    #await ctx.message.add_reaction(emoji)

@bot.command(help = "Save a new quote.", aliases=['add','addquote'])
async def addQuote(ctx, quoteAuthor, *, quote = None):
    quoteAuthor = bot.get_cog("Alias").fetchAlias(quoteAuthor)[1]
    try:
        date = datetime.date.today()
    except Exception as e:
        Printer(e)
    
    if ctx.message.attachments:
        if(ctx.message.attachments[0].size > constants.MAX_FILESIZE):
            receivedSize = str(ctx.message.attachments[0].size/1000000)
            maxSize = str(constants.MAX_FILESIZE/1000000)
            await ctx.channel.send("This file is too large. (Received Size: " + receivedSize + " MB, Max Size: " + maxSize + " MB)")
            return

        fileExtension = ctx.message.attachments[0].filename #Probably a better way to do this, but I don't know how.
        fileExtension = fileExtension.rsplit('.', 1)[-1] #All text after last dot. If filename has no dot, entire filename will be saved. This is bad.
    elif quote:
        fileExtension = None
    else:
        await ctx.channel.send("No quote provided.")
        return
    
    cur = con.cursor()
    cur.execute("INSERT INTO quotes(quote, quoteAuthor, quoteRecorder, date, fileExtension) VALUES (?, ?, ?, ?, ?)", (quote, quoteAuthor, ctx.author.name, date, fileExtension))

    if(ctx.message.attachments): #Save message attachment.
        await ctx.message.attachments[0].save(config["Attachments"] + str(cur.lastrowid) + '.' + fileExtension)
        #Attachment filename is based on unique id of the quote.
        #Saved files will never have the same filename.
        #Only one attachment can be saved per quote.

    con.commit()
    await ctx.channel.send("Quote #" + str(cur.lastrowid) + " saved.")
    await ctx.message.add_reaction(emoji)

@bot.command(help = "Reload extensions.")
async def refreshCommands(ctx):
    for extension in extensions:
        await bot.reload_extension(extension)
    await ctx.send("Commands synced.")

bot.run(config["Token"], reconnect=True)
#end command lets the client know that it is a bot
#also if connection drops, bot will attempt to reconnect
#saves trouble of manually restarting in the event of connection loss
