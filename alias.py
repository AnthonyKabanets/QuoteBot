import sqlite3
from discord.ext import commands

class Alias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        aliasDB = "aliases.db"
        self.con = sqlite3.connect(aliasDB)
        
        #Check if table exists, if it doesn't create it.
        cur = self.con.cursor()
        cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='alias' ''')
        if(cur.fetchone()[0] == 0) : {
            cur.execute('''CREATE TABLE alias
                            (inputName text NOT NULL, 
                            outputName text NOT NULL)''')
        }
    
    #Will return a (Bool, String) tuple.
    #Bool represents whether an alias was found.
    #If not found, string is the inputName. If found, string is the resulting alias.
    def fetchAlias(self, inputName):
        cur = self.con.cursor()
        cur.execute("SELECT outputName FROM alias WHERE inputName=:name ", {"name": inputName})
        output = cur.fetchone()
        if output is None: #No rows matching name found.
            return (False, inputName)
        
        return (True, output[0])
    
    @commands.command(help = "Adds an alias for a provided name, which redirects requests to another name.")
    async def addAlias(self, ctx, inputName, outputName):
        cur = self.con.cursor()
        cur.execute("SELECT inputName, outputName FROM alias WHERE inputName=:name ", {"name": inputName})
        check = self.fetchAlias(inputName)
        if check[0]: #Alias already exists for this inputName
            await ctx.channel.send(inputName + " is already aliased to " + check[1])
            return
        
        cur.execute("INSERT INTO alias(inputName, outputName) VALUES (?,?)", (inputName, outputName))
        self.con.commit()
        await ctx.channel.send(inputName + " is now aliased to " + outputName)
    
    @commands.command(help = "Removes an alias for a provided name.")
    async def removeAlias(self, ctx, inputName, outputName):
        cur = self.con.cursor()
        cur.execute("DELETE FROM alias WHERE inputName = :inputName AND outputName = :outputName", {"inputName": inputName, "outputName": outputName})
        cur.execute("SELECT changes()")
        rowsDeleted = cur.fetchone()[0]
        await ctx.channel.send("Deleted " + str(rowsDeleted) + " alias(es).")
        self.con.commit()