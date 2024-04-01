import sqlite3
import discord
from discord.ext import commands

class Alias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        
        aliasDB = "aliases.db"
        self.con = sqlite3.connect(aliasDB)
        self.cur = self.con.cursor()
        #Check if table exists, if it doesn't create it.
        self.cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='alias' ''')
        if(self.cur.fetchone()[0] == 0) : {
            self.cur.execute('''CREATE TABLE alias
                            (inputName text NOT NULL, 
                            outputName text NOT NULL)''')
        }
    
    #Will return a (Bool, String) tuple.
    #Bool represents whether an alias was found.
    #If not found, string is the inputName. If found, string is the resulting alias.
    def fetchAlias(self, inputName):
        self.cur.execute("SELECT outputName FROM alias WHERE inputName=:name ", {"name": inputName})
        output = self.cur.fetchone()
        if output is None: #No rows matching name found.
            return (False, inputName)
        
        return (True, output[0])
    
    @commands.command()
    async def addAlias(self, ctx, inputName, outputName):
        self.cur.execute("SELECT inputName, outputName FROM alias WHERE inputName=:name ", {"name": inputName})
        check = self.fetchAlias(inputName)
        if check[0]: #Alias already exists for this inputName
            await ctx.channel.send(inputName + " is already aliased to " + check[1])
            return
        
        self.cur.execute("INSERT INTO alias(inputName, outputName) VALUES (?,?)", (inputName, outputName))
        self.con.commit()
        await ctx.channel.send(inputName + " is now aliased to " + outputName)