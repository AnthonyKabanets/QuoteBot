import discord
import asyncio
from datetime import datetime
from datetime import date
import time
from quoteflags import QuoteFlags, QuoteMetadata
from discord.ext import commands
from helpers import getConfig
import constants
from helpers import QuoteHelpers
from typing import Optional

async def setup(bot):
    await bot.add_cog(Quote(bot))

class Quote(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.con = bot.db_connection

    @commands.command(help = "Prints how many times a person has been quoted.")
    async def quotedCount(self, ctx, quoteAuthor):
        quoteAuthor = self.bot.get_cog("Alias").fetchAlias(quoteAuthor)[1]
        cur = self.con.cursor()
        cur.execute("SELECT COUNT() FROM authors WHERE author = :name", {"name": quoteAuthor})
        quoteCount = cur.fetchone()[0]
        await ctx.channel.send(quoteAuthor + " has " + str(quoteCount) + " quotes.")
        #await ctx.message.add_reaction(emoji)

    @commands.command(help = "Prints the top quoted people.", aliases=['quoteRank'])
    async def rank(self, ctx, *, flags: QuoteFlags):
        if flags.count == 1: 
            flags.count = 5
        dateMin = datetime.strptime(flags.dateStart, flags.dateFormat).date()
        dateMax = datetime.strptime(flags.dateEnd, flags.dateFormat).date()
        cur = self.con.cursor()
        cur.execute("SELECT author, COUNT(author), date FROM authors JOIN quotes ON authors.id = quotes.id \
                    WHERE date > :dateMin GROUP BY author \
                    ORDER BY COUNT(author) DESC LIMIT :numAuthors", 
                    {"numAuthors": flags.count, "dateMin": dateMin, "dateMax": dateMax})
        rows = cur.fetchall()
        tempString = ""
        for row in rows:
            tempString += ("Name: " + str(row[0]) + "\n    Quotes: " + str(row[1]) + "\n")
        
        cur.close()
        await ctx.send(tempString)

    @commands.command(help = "Prints the number of times a user has added quotes.")
    async def quoterCount(self, ctx, quoteRecorder):
        cur = self.con.cursor()
        cur.execute("SELECT COUNT() FROM quotes WHERE quoteRecorder = :name", {"name": quoteRecorder.lower()})
        quoteCount = cur.fetchone()[0]
        cur.close()
        await ctx.channel.send(quoteRecorder + " has recorded " + str(quoteCount) + " quotes.")
        #await ctx.message.add_reaction(emoji)

    @commands.command(help = "Prints the total number of quotes saved.")
    async def totalQuotes(self, ctx):
        cur = self.con.cursor()
        cur.execute("SELECT COUNT() FROM quotes")
        quoteCount = cur.fetchone()[0]
        cur.close()
        await ctx.channel.send(str(quoteCount) + " quotes recorded.")
        #await ctx.message.add_reaction(emoji)
    
    #This could push a very long quote past the length limit. 
    #TODO: Check messageLenInBounds before allowing.
    @commands.command(help = "Add an author to an existing quote.")
    async def addAuthor(self, ctx, quoteID, quoteAuthor):
        cur= self.con.cursor()
        cur.execute("SELECT count(authors.id) FROM authors WHERE authors.id = :id", {"id": quoteID})
        idCount = cur.fetchone()[0]
        if idCount == 0:
            await ctx.channel.send("No quote with chosen ID exists.")
            return
        
        cur.execute("SELECT count(authors.id) FROM authors WHERE authors.id = :id AND authors.author = :author", {"id": quoteID, "author": quoteAuthor})
        idCount = cur.fetchone()[0]
        if idCount > 0:
            await ctx.channel.send("Quote already attributed to this author.")
            return

        cur.execute("INSERT INTO authors(id, author) VALUES (?, ?)", (quoteID, quoteAuthor))
        cur.close()
        self.con.commit()
        await ctx.message.add_reaction(getConfig("Emoji"))
    
    @commands.command(help = "Remove an author from an existing quote. Can cause quotes to have no author.")
    async def removeAuthor(self, ctx, quoteID, quoteAuthor):
        cur = self.con.cursor()
        cur.execute("SELECT count(authors.id) FROM authors WHERE authors.id = :id AND authors.author = :author", {"id": quoteID, "author": quoteAuthor})
        idCount = cur.fetchone()[0]
        if idCount == 0:
            await ctx.channel.send("Quote already not attributed to this author.")
            return
        
        cur.execute("DELETE FROM authors WHERE authors.id = :id AND authors.author = :author", {"id": quoteID, "author": quoteAuthor})
        cur.close()
        self.con.commit()
        await ctx.message.add_reaction(getConfig("Emoji"))
    
    @commands.command(help = "Replaces all authors on a quote.")
    async def editAuthors(self, ctx, quoteID, authors):
        cur = self.con.cursor()
        cur.execute("DELETE FROM authors WHERE authors.id = :id", {"id": quoteID})
        
        authorList = authors.split(',')
        for author in authorList:
            alias = self.bot.get_cog("Alias").fetchAlias(author)[1]
            cur.execute("INSERT INTO authors(id, author) VALUES (?, ?)", (quoteID, alias))
        cur.close()
        self.con.commit()
        await ctx.message.add_reaction(getConfig("Emoji"))
    
    #Edit text or attachments of a quote without changing the ID, dates, or authors.
    @commands.command(help = "Edit text or attachments of an existing quote.", aliases=['edit'])
    async def editQuote(self, ctx, id, *, quote = None):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM quotes WHERE id = :id", {"id": id})
        quoteRow = cur.fetchone()
        #Check quote row to keep metadata, no need to check attachments row.
        #cur.execute("SELECT * FROM attachments WHERE id = :id", {"id": id})
        #attachmentRow = cur.fetchall()

        cur.execute("DELETE FROM quotes WHERE id = :id", {"id": id})
        cur.execute("DELETE FROM attachments WHERE id = :id", {"id": id})
        quoteRecorder = quoteRow[2]
        quoteDate = quoteRow[3]
        try:
            cur.execute("INSERT INTO quotes(quote, quoteRecorder, date, id) VALUES (?, ?, ?, ?)", (quote, quoteRecorder, quoteDate, id))
            if ctx.message.attachments:
                await QuoteHelpers.parseAttachments(ctx, id, self.con)
        except Exception as e:
            self.con.rollback()
            raise e
        cur.close()
        self.con.commit()
        await ctx.message.add_reaction(getConfig("Emoji"))

    @commands.command(help = "Save a new quote.", aliases=['add','addquote'])
    async def addQuote(self, ctx, id: Optional[int], quoteAuthor, *, quote = None):
        if not id: #Optional id prevents any author from having a purely numerical name.
            id = -1
        
        authorList = quoteAuthor.split(',')
        aliasList = []
        for author in authorList:
            aliasList.append(self.bot.get_cog("Alias").fetchAlias(author)[1])
        authorList = aliasList
        
        today = 0
        try:
            today = date.today()
        except Exception as e:
            print(e)
            raise e
        
        if not ctx.message.attachments and not quote:
            await ctx.channel.send("No quote provided.")
            return

        if id != -1 and QuoteHelpers.idAlreadyUsed(self.con, id):
            ctx.channel.send("ID already in use.")
            return

        try:
            quoteID = await QuoteHelpers.insertQuote(ctx, self.con, authorList, quote, today, id)
            #Attachment filename is based on unique id of the quote.
            #Saved files will never have the same filename.

            messageLen = len(QuoteHelpers.genQuoteString(quote, quoteAuthor, str(today), quoteID)) + len(authorList)
            if constants.MAX_LENGTH < messageLen:
                #Using quoteAuthor instead of authorList to include commas.
                await ctx.channel.send("Message too long!")
                raise Exception("Message too long!")

            self.con.commit()
            await ctx.channel.send("Quote #" + str(quoteID) + " saved.")
            await ctx.message.add_reaction(getConfig("Emoji"))
        except Exception as e:
            self.con.rollback()
            raise e

    async def printQuote(ctx, output, authors, attachments): #output comes from cur.fetchone()
        if(output is None):
            await ctx.channel.send("No valid quotes found.")
            return
        
        outputString = QuoteHelpers.genQuoteString(output[1], authors, output[4], output[0])
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

    @commands.command(help = "Prints the quote with a specific ID.")
    async def idQuote(self, ctx, id):
        cur = self.con.cursor()
        cur.execute("SELECT quotes.id, quote, author, quoteRecorder, date FROM authors JOIN quotes on authors.id = quotes.id WHERE authors.id = :id", {"id": id})
        output = cur.fetchone()
        cur.close()
        
        authors = QuoteHelpers.genAuthorString(self.con, id)
        attachments = QuoteHelpers.genAttachmentStrings(self.con, id)
        await Quote.printQuote(ctx, output, authors, attachments)
        await ctx.message.add_reaction(getConfig("Emoji"))
    
    @commands.command(help = "Prints a random quote.")
    async def quote(self, ctx, quoteAuthor, *, flags: QuoteFlags):
        try:
            quoteAuthor = self.bot.get_cog("Alias").fetchAlias(quoteAuthor)[1]
            numQuotes = min(max(flags.count, constants.MIN_REQUEST), constants.MAX_REQUEST)
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
                    authors = QuoteHelpers.genAuthorString(self.con, quote[0])
                    attachments = QuoteHelpers.genAttachmentStrings(self.con, quote[0])
                    await Quote.printQuote(ctx, quote, authors, attachments)
                    time.sleep(0.3)
            else:
                await ctx.channel.send("No quotes found.")
            await ctx.message.add_reaction(getConfig('Emoji'))
        except Exception as e:
            print(e)
    
    @commands.command(help = "Set date or recorder for a quote.")
    async def updateMetadata(self, ctx, id, *, flags: QuoteMetadata):
        cur = self.con.cursor()
        cur.execute("SELECT date, quoteRecorder FROM quotes WHERE id = :id", {"id": id})
        output = cur.fetchone()
        
        if flags.date == "":
            date = output[0]
        else:
            date = datetime.strptime(flags.date, flags.dateFormat).date()
        
        if flags.recorder == "":
            flags.recorder = output[1]

        cur.execute("UPDATE quotes SET date = :date, quoteRecorder = :recorder WHERE id = :id", 
                    {"date": date, "recorder": flags.recorder, "id": id})
        
        cur.close()
        self.con.commit()
        await ctx.message.add_reaction(getConfig('Emoji'))