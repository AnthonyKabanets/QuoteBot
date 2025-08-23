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
    

@bot.command(help = "Prints how many times a person has been quoted.")
async def quotedCount(ctx, quoteAuthor):
    quoteAuthor = bot.get_cog("Alias").fetchAlias(quoteAuthor)[1]
    cur = con.cursor()
    cur.execute("SELECT COUNT() FROM authors WHERE author = :name", {"name": quoteAuthor})
    quoteCount = cur.fetchone()[0]
    await ctx.channel.send(quoteAuthor + " has " + str(quoteCount) + " quotes.")
    #await ctx.message.add_reaction(emoji)

@bot.command(help = "Prints the top quoted people.", aliases=['quoteRank'])
async def rank(ctx, numquotes=5):
    cur = con.cursor()
    cur.execute("SELECT author, COUNT(author) FROM authors GROUP BY author ORDER BY COUNT(author) DESC LIMIT :numQuotes", {"numQuotes": numquotes})
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

import mimetypes
async def parseAttachments(ctx, quoteID, cursor):
    for attachment in ctx.message.attachments:
        if(attachment.size > constants.MAX_FILESIZE):
            receivedSize = str(attachment.size/1000000)
            maxSize = str(constants.MAX_FILESIZE/1000000)
            await ctx.channel.send("This file is too large. (Received Size: " + receivedSize + " MB, Max Size: " + maxSize + " MB)")
            return -1
    
    index = 0
    for attachment in ctx.message.attachments:
        fileType = ctx.message.attachments[0].content_type
        fileExtension = mimetypes.guess_extension(fileType, strict=False)
        if fileExtension is None:
            ctx.channel.send("Couldn't parse file extension.")
            raise "Couldn't parse file extension."

        fileName = str(quoteID)
        fileIndex = None
        if index > 0: 
            fileIndex = index
            fileName += "_" + str(index)
        fileName += fileExtension
        row = (quoteID, fileIndex, fileExtension)
        cursor.execute("INSERT INTO attachments(id, fileIndex, extension) VALUES (?, ?, ?)", row)
        index += 1
        
        await attachment.save(config["Attachments"] + fileName)
    #fileExtension = ctx.message.attachments[0].filename #Probably a better way to do this, but I don't know how.
    #fileExtension = fileExtension.rsplit('.', 1)[-1] #All text after last dot. If filename has no dot, entire filename will be saved. This is bad.
    

@bot.command(help = "Save a new quote.", aliases=['add','addquote'])
async def addQuote(ctx, quoteAuthor, *, quote = None):
    authorList = quoteAuthor.split(',')
    aliasList = []
    for author in authorList:
        aliasList.append(bot.get_cog("Alias").fetchAlias(author)[1])
    authorList = aliasList
    try:
        date = datetime.date.today()
    except Exception as e:
        print(e)
    
    if not ctx.message.attachments and not quote:
        await ctx.channel.send("No quote provided.")
        return
    
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO quotes(quote, quoteRecorder, date) VALUES (?, ?, ?)", (quote, ctx.author.name, date))
        cur.execute("SELECT last_insert_rowid()")
        output = cur.fetchone()
        quoteID = output[0]
        for author in authorList:
            cur.execute("INSERT INTO authors(id, author) VALUES (?, ?)", (quoteID, author))

        if ctx.message.attachments:
            res = await parseAttachments(ctx, quoteID, cur)
            if res == -1:
                con.rollback()
                return
        #Attachment filename is based on unique id of the quote.
        #Saved files will never have the same filename.

        con.commit()
        await ctx.channel.send("Quote #" + str(quoteID) + " saved.")
        await ctx.message.add_reaction(emoji)
    except Exception as e:
        con.rollback()
        raise e


@bot.command(help = "Reload extensions.")
async def refreshCommands(ctx):
    for extension in extensions:
        await bot.reload_extension(extension)
    await ctx.send("Commands synced.")

bot.run(config["Token"], reconnect=True)
#end command lets the client know that it is a bot
#also if connection drops, bot will attempt to reconnect
#saves trouble of manually restarting in the event of connection loss
