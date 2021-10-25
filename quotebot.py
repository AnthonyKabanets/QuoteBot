import discord
from discord.ext import commands
import logging
import sqlite3
import datetime

logging.basicConfig(level=logging.INFO)

bot = commands.Bot(command_prefix='$')

con = sqlite3.connect('quotes.db')
cur = con.cursor()

cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='quotes' ''')

if(cur.fetchone()[0] == 0) : {
    cur.execute('''CREATE TABLE quotes 
                    #(quote text, quoteAuthor text, quoteRecorder text, date date)''')
}

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

#@bot.event
#async def on_message(message):
    #if message.author == bot.user:
        #return

    #if message.content.startswith('$hello'):
        #await message.channel.send('Hello!')

@bot.command()
async def test(ctx):
    await ctx.channel.send('Hello World!')

@bot.command()
async def quote(ctx, quoteAuthor, *, quote = None):
    if(quote is None):
        cur.execute("SELECT * FROM quotes WHERE quoteAuthor = :name ORDER BY RANDOM() LIMIT 1", {"name": quoteAuthor})
        output = cur.fetchone()
        if(output is None):
            await ctx.channel.send("No valid quotes found.")
        else:
            await ctx.channel.send(output[0] + '\n-' + output[1])
        #[0][0] takes the first result from the command, and selects the column out of the row.
    else:
        date = datetime.date.today()
        quote_list = [
            (quote, quoteAuthor, ctx.author.name, date)
        ]
        print(quote)
        print(quoteAuthor)
        print(ctx.author.name)
        print(date)
        cur.executemany("INSERT INTO quotes VALUES (?, ?, ?, ?)", quote_list)
        con.commit()
        await ctx.message.add_reaction('✅')
        #Instead of reaction, send message. Then, if someone reacts with 🚫, remove that quote.
        #Or just use DB viewer to personally delete mistaken quotes.



bot.run('your key here')