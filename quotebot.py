import discord
from discord.emoji import Emoji
from discord.ext import commands
from discord.reaction import Reaction

import logging
import sqlite3
import datetime
import time

import quoteflags
import alias
import constants
import admin
import helpers
import Printer
from Printer import Print

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
helpers.initTable(con, 'quotes') #Make quotes table if it does not exist.

printManager = Printer.initPrint(bot, con)
adminManager = admin.Admin(bot, con)
aliasManager = alias.Alias(bot)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    await bot.add_cog(printManager)
    await bot.add_cog(aliasManager) #Adding commands from alias.py
    await bot.add_cog(adminManager)
    

@bot.command(help = "Prints how many times a person has been quoted.")
async def quotedCount(ctx, quoteAuthor):
    quoteAuthor = aliasManager.fetchAlias(quoteAuthor)[1]
    cur = con.cursor()
    cur.execute("SELECT COUNT() FROM quotes WHERE quoteAuthor = :name", {"name": quoteAuthor})
    quoteCount = cur.fetchone()[0]
    await ctx.channel.send(quoteAuthor + " has " + str(quoteCount) + " quotes.")
    #await ctx.message.add_reaction(emoji)

@bot.command(help = "Prints the top quoted people.")
async def quoteRank(ctx, numQuotes=5):
    cur = con.cursor()
    cur.execute("SELECT quoteAuthor, COUNT(quoteAuthor) FROM quotes GROUP BY quoteAuthor ORDER BY COUNT(quoteAuthor) DESC LIMIT :numQuotes", {"numQuotes": numQuotes})
    rows = cur.fetchall()
    tempString = ""
    for row in rows:
        tempString += ("Name: " + str(row[0]) + "\n    Quotes: " + str(row[1]) + "\n")
    
    await ctx.channel.send(tempString)

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



@bot.command(help = "Save a new quote.")
async def addQuote(ctx, quoteAuthor, *, quote = None):
    quoteAuthor = aliasManager.fetchAlias(quoteAuthor)[1]
    try:
        date = datetime.date.today()
    except Exception as e:
        Printer(e)
    
    if ctx.message.attachments:
        if(ctx.message.attachments[0].size > constants.MAX_FILESIZE): #Capped at 8 MB. Bot cannot send files larger than 8 MB.
            await ctx.message.send("This file is too large.")
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

@bot.command(help = "Prints a random quote.")
async def quote(ctx, quoteAuthor, numQuotes = 1, *, flags: quoteflags.QuoteFlags):
    try:
        quoteAuthor = aliasManager.fetchAlias(quoteAuthor)[1]
        numQuotes = min(max(numQuotes, constants.MIN_REQUEST), constants.MAX_REQUEST) #Min is 1, max is 20.
        
        dateMin = datetime.datetime.strptime(flags.dateStart, flags.dateFormat).date()
        dateMax = datetime.datetime.strptime(flags.dateEnd, flags.dateFormat).date()
        cur = con.cursor()
        cur.execute("SELECT * FROM quotes WHERE quoteAuthor = :name AND id > :idMin AND id < :idMax AND date > :dateMin AND date < :dateMax ORDER BY RANDOM() LIMIT :numQuotes", 
                    {"name": quoteAuthor, "numQuotes": numQuotes, 
                    "idMin": flags.idMin, "idMax": flags.idMax,
                    "dateMin": dateMin, "dateMax": dateMax})
        output = cur.fetchall()

        if(output):
            for quote in output:
                await Print.printQuote(ctx, quote)
                time.sleep(0.3)
        else:
            await ctx.channel.send("No quotes found.")
        await ctx.message.add_reaction(emoji)
    except Exception as e:
        print(e)

bot.run(config["Token"], reconnect=True)
#end command lets the client know that it is a bot
#also if connection drops, bot will attempt to reconnect
#saves trouble of manually restarting in the event of connection loss
