import discord
import asyncio
from datetime import datetime
import time
from quoteflags import QuoteFlags
from discord.ext import commands
from helpers import getConfig
import constants
import mimetypes

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
    async def rank(self, ctx, numquotes=5):
        cur = self.con.cursor()
        cur.execute("SELECT author, COUNT(author) FROM authors GROUP BY author ORDER BY COUNT(author) DESC LIMIT :numQuotes", {"numQuotes": numquotes})
        rows = cur.fetchall()
        tempString = ""
        for row in rows:
            tempString += ("Name: " + str(row[0]) + "\n    Quotes: " + str(row[1]) + "\n")
        
        await ctx.send(tempString)

    @commands.command(help = "Prints the number of times a user has added quotes.")
    async def quoterCount(self, ctx, quoteRecorder):
        cur = self.con.cursor()
        cur.execute("SELECT COUNT() FROM quotes WHERE quoteRecorder = :name", {"name": quoteRecorder})
        quoteCount = cur.fetchone()[0]
        await ctx.channel.send(quoteRecorder + " has recorded " + str(quoteCount) + " quotes.")
        #await ctx.message.add_reaction(emoji)

    @commands.command(help = "Prints the total number of quotes saved.")
    async def totalQuotes(self, ctx):
        cur = self.con.cursor()
        cur.execute("SELECT COUNT() FROM quotes")
        quoteCount = cur.fetchone()[0]
        await ctx.channel.send(str(quoteCount) + " quotes recorded.")
        #await ctx.message.add_reaction(emoji)
    
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
            
            await attachment.save(getConfig("Attachments") + fileName)
    

    @commands.command(help = "Save a new quote.", aliases=['add','addquote'])
    async def addQuote(self, ctx, quoteAuthor, *, quote = None):
        authorList = quoteAuthor.split(',')
        aliasList = []
        for author in authorList:
            aliasList.append(self.bot.get_cog("Alias").fetchAlias(author)[1])
        authorList = aliasList
        try:
            date = datetime.date.today()
        except Exception as e:
            print(e)
        
        if not ctx.message.attachments and not quote:
            await ctx.channel.send("No quote provided.")
            return
        
        try:
            cur = self.con.cursor()
            cur.execute("INSERT INTO quotes(quote, quoteRecorder, date) VALUES (?, ?, ?)", (quote, ctx.author.name, date))
            cur.execute("SELECT last_insert_rowid()")
            output = cur.fetchone()
            quoteID = output[0]
            for author in authorList:
                cur.execute("INSERT INTO authors(id, author) VALUES (?, ?)", (quoteID, author))

            if ctx.message.attachments:
                res = await Quote.parseAttachments(ctx, quoteID, cur)
                if res == -1:
                    self.con.rollback()
                    return
            #Attachment filename is based on unique id of the quote.
            #Saved files will never have the same filename.

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
                    authors = Quote.genAuthorString(self.con, quote[0])
                    attachments = self.genAttachmentStrings(quote[0])
                    await Quote.printQuote(ctx, quote, authors, attachments)
                    time.sleep(0.3)
            else:
                await ctx.channel.send("No quotes found.")
            await ctx.message.add_reaction(getConfig('Emoji'))
        except Exception as e:
            print(e)