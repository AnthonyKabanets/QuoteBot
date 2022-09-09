import discord
from discord.emoji import Emoji
from discord.ext import commands
import logging
import sqlite3
import os
import datetime
import time
from discord.reaction import Reaction

#ruamel is just a nicer json tbh
#will need to install library for it first, however
#pip install ruamel.yaml
from ruamel.yaml import YAML
yaml = YAML()

with open("config.yaml", "r", encoding = "utf-8") as file: #utf-8 as standard
    config = yaml.load(file)

logging.basicConfig(level=logging.INFO)

botIntents = discord.Intents.default()
botIntents.message_content = True
bot = commands.Bot(command_prefix=config["Prefix"], intents = botIntents)
emoji = '✅'

con = sqlite3.connect(config['Quotes'])
cur = con.cursor()

cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='quotes' ''')

if(cur.fetchone()[0] == 0) : {
    cur.execute('''CREATE TABLE quotes 
                    (id integer NOT NULL PRIMARY KEY, 
                    quote text, 
                    quoteAuthor text NOT NULL, 
                    quoteRecorder text NOT NULL, 
                    date date, 
                    fileExtension text)''')
}

async def printQuote(ctx, output): #output comes from cur.fetchone()
    if(output is None):
        await ctx.channel.send("No valid quotes found.")
    else:
        outputString = content=str(output[1] or '') + '\n-' + output[2] + ', ' + output[4] + ", ID: " + str(output[0])
        if(output[5]): #output[5] is file extension column.
            file = discord.File(config["Attachments"] + str(output[0]) + '.' + output[5])
            await ctx.channel.send(file = file, content=outputString)
        else:
            await ctx.channel.send(outputString)
#[0][0] takes the first result from fetchmany, and selects the column out of the row.

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    #sets status of game to "listening"
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=config["Presence"]))
    #await bot.change_presence(activity=config["Presence"]) apparently you cant just set a status without some extra steps. wip - rahat

@bot.command()
async def test(ctx):
    await ctx.channel.send('Hello World!')

@bot.command()
async def quotedCount(ctx, quoteAuthor):
    cur.execute("SELECT COUNT() FROM quotes WHERE quoteAuthor = :name", {"name": quoteAuthor})
    quoteCount = cur.fetchone()[0]
    await ctx.channel.send(quoteAuthor + " has " + str(quoteCount) + " quotes.")
    #await ctx.message.add_reaction(emoji)

@bot.command()
async def quoteRank(ctx, numQuotes):
    cur.execute("SELECT quoteAuthor, COUNT(quoteAuthor) FROM quotes GROUP BY quoteAuthor ORDER BY COUNT(quoteAuthor) DESC LIMIT :numQuotes", {"numQuotes": numQuotes})
    rows = cur.fetchall()
    tempString = ""
    for row in rows:
        tempString += ("Name: " + str(row[0]) + "\n    Quotes: " + str(row[1]) + "\n")
    
    await ctx.channel.send(tempString)

@bot.command()
async def quoterCount(ctx, quoteRecorder):
    cur.execute("SELECT COUNT() FROM quotes WHERE quoteRecorder = :name", {"name": quoteRecorder})
    quoteCount = cur.fetchone()[0]
    await ctx.channel.send(quoteRecorder + " has recorded " + str(quoteCount) + " quotes.")
    #await ctx.message.add_reaction(emoji)

@bot.command()
async def totalQuotes(ctx):
    cur.execute("SELECT COUNT() FROM quotes")
    quoteCount = cur.fetchone()[0]
    await ctx.channel.send(str(quoteCount) + " quotes recorded.")
    #await ctx.message.add_reaction(emoji)

@bot.command()
async def idQuote(ctx, id):
    cur.execute("SELECT * FROM quotes WHERE id = :id", {"id": id})
    output = cur.fetchone()
    await printQuote(ctx, output)
    #await ctx.message.add_reaction(emoji)

@bot.command()
async def addQuote(ctx, quoteAuthor, *, quote = None):
    date = datetime.date.today()
    if ctx.message.attachments:
        if(ctx.message.attachments[0].size > 8000000): #Capped at 8 MB. Bot cannot send files larger than 8 MB.
            await ctx.message.send("This file is too large.")
            return

        fileExtension = ctx.message.attachments[0].filename #Probably a better way to do this, but I don't know how.
        fileExtension = fileExtension.rsplit('.', 1)[-1] #All text after last dot. If filename has no dot, entire filename will be saved. This is bad.
    elif quote:
        fileExtension = None
    else:
        await ctx.channel.send("No quote provided.")
        return
    
    cur.execute("INSERT INTO quotes(quote, quoteAuthor, quoteRecorder, date, fileExtension) VALUES (?, ?, ?, ?, ?)", (quote, quoteAuthor, ctx.author.name, date, fileExtension))

    if(ctx.message.attachments): #Save message attachment.
        await ctx.message.attachments[0].save(config["Attachments"] + str(cur.lastrowid) + '.' + fileExtension)
        #Attachment filename is based on unique id of the quote.
        #Saved files will never have the same filename.
        #Only one attachment can be saved per quote.

    con.commit()
    await ctx.channel.send("Quote #" + str(cur.lastrowid) + " saved.")
    await ctx.message.add_reaction(emoji)

@bot.command()
async def quote(ctx, quoteAuthor, numQuotes = 1):
    #cur.execute("SELECT COUNT() FROM quotes WHERE quoteAuthor = :name", {"name": quoteAuthor})
    if(numQuotes < 1):
        numQuotes = 1
    if(numQuotes > 20):
        numQuotes = 20 #Min is 1, max is 20.
    
    cur.execute("SELECT * FROM quotes WHERE quoteAuthor = :name ORDER BY RANDOM() LIMIT :numQuotes", {"name": quoteAuthor, "numQuotes": numQuotes})
    output = cur.fetchall()

    if(output):
        for quote in output:
            await printQuote(ctx, quote)
            time.sleep(0.3)
    else:
        await ctx.channel.send("No quotes found.")
    await ctx.message.add_reaction(emoji)

@bot.command()
@commands.has_role(config["Permissions Role"])
async def deleteQuote (ctx, id):
    await ctx.channel.send("Deleting quote...")
    await idQuote(ctx, id)
    cur.execute("SELECT * FROM quotes WHERE id = :id", {"id": id})
    output = cur.fetchone()
    if(output is None):
        return

    if(output[5]): #Deleting saved attachment.
        os.remove(config["Attachments"] + str(id) + "." + output[5])

    cur.execute("DELETE FROM quotes WHERE id = :id", {"id": id})
    con.commit()
    await ctx.message.add_reaction(emoji)
    #id is primary key, this should never delete more than one quote.

@bot.event
async def on_command_error(ctx, error):
    if(isinstance(error, commands.MissingRole)):
        await ctx.send("Required role missing.")
    elif(isinstance(error, commands.CommandNotFound)):
        await ctx.send("Command not found.")

#restart the bot
@bot.command(name ="restart", aliases = ["r"], help = "Restarts the bot.")
@commands.has_role(config["Permissions Role"])
async def restart(ctx): #ctx passes an argument into the body. a "context" (ctx)
    #sends react to message as confirmation to restart
    await ctx.message.add_reaction(emoji)
    con.close()
    await bot.close()
    

bot.run(config["Token"], reconnect=True)
#end command lets the client know that it is a bot
#also if connection drops, bot will attempt to reconnect
#saves trouble of manually restarting in the event of connection loss
