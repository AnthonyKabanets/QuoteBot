import sqlite3
import discord
import asyncio
from datetime import datetime
import time
from quoteflags import QuoteFlags
from discord.ext import commands
from helpers import getConfig
import constants

async def setup(bot):
    await bot.add_cog(Print(bot))

class Print(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.con = bot.db_connection

    async def printQuote(ctx, output): #output comes from cur.fetchone()
        if(output is None):
            await ctx.channel.send("No valid quotes found.")
            return

        outputString = str(output[1] or '') + '\n-# -' + output[2] + ', ' + output[4] + ", ID: " + str(output[0])
        try:
            if(output[5]): #output[5] is file extension column.
                file = discord.File(getConfig("Attachments") + str(output[0]) + '.' + output[5])
                msg = await ctx.channel.send(file = file, content=outputString)
            else:
                msg = await ctx.channel.send(outputString)
            
            async def reactionDelete(): #Put in a function for create_task
                def check(reaction, user):
                        return user == ctx.message.author and reaction.message == msg and reaction.emoji == getConfig("EmojiCancel")
                try:
                    reaction, user = await ctx.bot.wait_for('reaction_add', timeout=15.0, check=check)
                except asyncio.TimeoutError:
                    print("No request for deletion.")
                else:
                    await msg.delete()
            
            asyncio.create_task(reactionDelete()) #Allows for rest of function to continue going.
        except FileNotFoundError: 
            await ctx.channel.send("Attachment not found. Quote ID: " + str(output[0]))
    #[0][0] takes the zeroth result from fetchmany, and selects the zeroth column out of the row.  

    @commands.command(help = "Prints the quote with a specific ID.")
    async def idQuote(self, ctx, id):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM quotes WHERE id = :id", {"id": id})
        output = cur.fetchone()
        cur.close()
        await Print.printQuote(ctx, output)
        await ctx.message.add_reaction(getConfig("Emoji"))
    
    @commands.command(help = "Prints a random quote.")
    async def quote(self, ctx, quoteAuthor, numQuotes = 1, *, flags: QuoteFlags):
        try:
            quoteAuthor = self.bot.get_cog("Alias").fetchAlias(quoteAuthor)[1]
            numQuotes = min(max(numQuotes, constants.MIN_REQUEST), constants.MAX_REQUEST)
            dateMin = datetime.strptime(flags.dateStart, flags.dateFormat).date()
            dateMax = datetime.strptime(flags.dateEnd, flags.dateFormat).date()
            cur = self.con.cursor()
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
            await ctx.message.add_reaction(getConfig('Emoji'))
        except Exception as e:
            print(e)