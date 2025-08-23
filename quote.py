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
    await bot.add_cog(Quote(bot))

class Quote(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.con = bot.db_connection

    async def printQuote(ctx, output, authors, attachments): #output comes from cur.fetchone()
        if(output is None):
            await ctx.channel.send("No valid quotes found.")
            return
        
        outputString = str(output[1] or '') + '\n-# -' + authors + ', ' + output[4] + ", ID: " + str(output[0])
        try:
            if len(attachments) > 0:
                files = []
                for attachment in attachments:
                    files.append(discord.File(getConfig("Attachments") + attachment))
                msg = await ctx.channel.send(files = files, content=outputString)
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

    def genAuthorString(con, id):
        cur = con.cursor()
        cur.execute("SELECT author FROM authors WHERE authors.id = :id", {"id": id})
        authorList = cur.fetchall()
        cur.close()
        if len(authorList) == 0: 
            return ""
        authorString = authorList[0][0]
        for author in authorList[1:]:
             authorString += ", " + author[0]
        return authorString

    def genAttachmentStrings(self, id):
        cur = self.con.cursor()
        cur.execute("SELECT fileIndex, extension FROM attachments WHERE attachments.id = :id", {"id": id})
        output = cur.fetchall()
        cur.close()
        fileNames = []
        for file in output:
            if file[0]:
                fileName = str(id) + "_" + str(file[0]) + file[1]
            else:
                fileName = str(id) + file[1]
            fileNames.append(fileName)
        return fileNames

    @commands.command(help = "Prints the quote with a specific ID.")
    async def idQuote(self, ctx, id):
        cur = self.con.cursor()
        cur.execute("SELECT quotes.id, quote, author, quoteRecorder, date FROM authors JOIN quotes on authors.id = quotes.id WHERE authors.id = :id", {"id": id})
        output = cur.fetchone()
        cur.close()
        
        authors = Quote.genAuthorString(self.con, id)
        attachments = self.genAttachmentStrings(id)
        await Quote.printQuote(ctx, output, authors, attachments)
        await ctx.message.add_reaction(getConfig("Emoji"))
    
    @commands.command(help = "Prints a random quote.")
    async def quote(self, ctx, quoteAuthor, numQuotes = 1, *, flags: QuoteFlags):
        try:
            quoteAuthor = self.bot.get_cog("Alias").fetchAlias(quoteAuthor)[1]
            numQuotes = min(max(numQuotes, constants.MIN_REQUEST), constants.MAX_REQUEST)
            dateMin = datetime.strptime(flags.dateStart, flags.dateFormat).date()
            dateMax = datetime.strptime(flags.dateEnd, flags.dateFormat).date()
            cur = self.con.cursor()
            cur.execute("SELECT quotes.id, quote, author, quoteRecorder, date FROM authors JOIN quotes ON authors.id = quotes.id AND author = :quoteAuthor WHERE \
                        authors.id > :idMin AND authors.id < :idMax \
                        AND date > :dateMin AND date < :dateMax \
                        ORDER BY RANDOM() LIMIT :numQuotes",
                        {"quoteAuthor": quoteAuthor, "numQuotes": numQuotes,
                         "idMin": flags.idMin, "idMax": flags.idMax, 
                         "dateMin": dateMin, "dateMax": dateMax})
            output = cur.fetchall()
            if(output):
                for quote in output:
                    authors = quote.genAuthorString(self.con, quote[0])
                    attachments = self.genAttachmentStrings(quote[0])
                    await quote.printQuote(ctx, quote, authors, attachments)
                    time.sleep(0.3)
            else:
                await ctx.channel.send("No quotes found.")
            await ctx.message.add_reaction(getConfig('Emoji'))
        except Exception as e:
            print(e)