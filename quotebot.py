import discord
from discord.emoji import Emoji
from discord.ext import commands
import logging
import sqlite3
import datetime
import json

from discord.reaction import Reaction

with open("config.json") as file:
    config = json.load(file)

logging.basicConfig(level=logging.INFO)

bot = commands.Bot(command_prefix=config["Prefix"])
#prefix is $
emoji = '✅'

con = sqlite3.connect(config['Quotes'])
cur = con.cursor()

cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='quotes' ''')

if(cur.fetchone()[0] == 0) : {
    cur.execute('''CREATE TABLE quotes 
                    (id integer NOT NULL PRIMARY KEY AUTOINCREMENT, 
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
        if(output[5]):
            file = discord.File(config["Attachments"] + str(output[0]) + '.' + output[5])
            await ctx.channel.send(file = file, content=outputString)
        else:
            await ctx.channel.send(outputString)
#[0][0] takes the first result from fetchmany, and selects the column out of the row.

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

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
async def quote(ctx, quoteAuthor, *, quote = None):
    if(quote is None and not ctx.message.attachments):
        cur.execute("SELECT * FROM quotes WHERE quoteAuthor = :name ORDER BY RANDOM() LIMIT 1", {"name": quoteAuthor})
        output = cur.fetchone()
        await printQuote(ctx, output)
    else:
        date = datetime.date.today()
        if(ctx.message.attachments):
            if(ctx.message.attachments[0].size > 8000000):
                await ctx.message.send("This file is too large.")
                return
            fileExtension = ctx.message.attachments[0].filename
            fileExtension = fileExtension.rsplit('.', 1)[-1]
        else:
           fileExtension = None
        
        cur.execute("INSERT INTO quotes(quote, quoteAuthor, quoteRecorder, date, fileExtension) VALUES (?, ?, ?, ?, ?)", (quote, quoteAuthor, ctx.author.name, date, fileExtension))

        if(ctx.message.attachments):
            await ctx.message.attachments[0].save(config["Attachments"] + str(cur.lastrowid) + '.' + fileExtension)

        con.commit()

    await ctx.message.add_reaction(emoji)

#restart the bot
@bot.command(name ="restart", aliases = ["r"], help = "Restarts the bot.")
async def restart(ctx): #ctx passes an argument into the body. a "context" (ctx)
    #sends react to message as confirmation to restart
    await ctx.message.add_reaction(emoji)
    con.close()
    await bot.close()

bot.run(config["Token"], bot=True, reconnect=True)
#end command lets the client know that it is a bot
#also if connection drops, bot will attempt to reconnect
#saves trouble of manually restarting in the event of connection loss
