import sqlite3
import os
from discord.ext import commands
from helpers import getConfig
import Printer

#Class for potentially destructive commands.
class Admin(commands.Cog):
    def __init__(self, bot, con: sqlite3.Connection): 
        self.bot = bot
        self.con = con
        
    @commands.command(help = "Deletes a quote with a specific ID. Requires permissions role.")
    @commands.has_role(getConfig("Permissions Role"))
    async def deleteQuote(self, ctx, id):
        await ctx.channel.send("Deleting quote...")
        await Printer.printManager.idQuote(ctx, id)
        cur = self.con.cursor()
        cur.execute("SELECT * FROM quotes WHERE id = :id", {"id": id})
        output = cur.fetchone()
        if(output is None):
            return

        if(output[5]): #Deleting saved attachment.
            os.remove(getConfig("Attachments") + str(id) + "." + output[5])

        cur.execute("DELETE FROM quotes WHERE id = :id", {"id": id})
        self.con.commit()
        await ctx.message.add_reaction(getConfig('Emoji'))
        #id is primary key, this should never delete more than one quote.
    
    #restart the bot
    @commands.command(name ="restart", aliases = ["r"], help = "Restarts the bot.")
    @commands.has_role(getConfig("Permissions Role"))
    async def restart(self, ctx): #ctx passes an argument into the body. a "context" (ctx)
        #sends react to message as confirmation to restart
        await ctx.message.add_reaction(getConfig('Emoji'))
        self.con.close()
        await self.bot.close()