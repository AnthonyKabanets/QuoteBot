import sqlite3
import discord
import asyncio
from discord.ext import commands
from helpers import getConfig

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

    @commands.command(help = "Prints the quote with a specific ID.")
    async def idQuote(self, ctx, id):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM quotes WHERE id = :id", {"id": id})
        output = cur.fetchone()
        cur.close()
        await Print.printQuote(ctx, output)
        await ctx.message.add_reaction(getConfig("Emoji"))