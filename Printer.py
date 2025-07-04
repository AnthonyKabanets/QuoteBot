import sqlite3
import discord
import asyncio
from discord.ext import commands
from helpers import getConfig

#In a separate file to avoid circular dependency with cogs that want to print quotes.
#Can't be instantiated form main because admin needs access to printManager instance.
printManager = None
def initPrint(bot, con): #Should always be called from quotebot.py before any admin.py can get at it.
    global printManager
    printManager = Print(bot, con)
    return printManager 
#Feels like it should be a singleton, but singletons can't have parameters.
#Maybe factory pattern would work better? Global object?

class Print(commands.Cog):
    def __init__(self, bot, con: sqlite3.Connection): 
        self.bot = bot
        self.con = con

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

    #async def fetchID(self, id): 
        

    @commands.command(help = "Prints the quote with a specific ID.")
    async def idQuote(self, ctx, id):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM quotes WHERE id = :id", {"id": id})
        output = cur.fetchone()
        await Print.printQuote(ctx, output)
        await ctx.message.add_reaction(getConfig("Emoji"))