from discord.ext import commands
from discord import Poll as d_poll
from discord import Embed
from discord import PollMedia
import datetime

async def setup(bot):
    await bot.add_cog(Polls(bot))

class Polls(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.con = bot.db_connection
    
    @commands.command(help = "Start a poll.")
    async def startPoll(self, ctx, category):
        cur = self.con.cursor()
        limit = 10
        cur.execute("SELECT quote, author, quoteRecorder FROM authors JOIN quotes ON authors.id = quotes.id AND author = :quoteAuthor \
                        ORDER BY RANDOM() LIMIT :numQuotes",
                        {"quoteAuthor": category, "numQuotes": limit})
        output = cur.fetchall()
        
        question = "Which " + str(category) + "?"
        duration = datetime.timedelta(hours=1)
        poll = d_poll(question=question,
                      duration=duration,
                      multiple=True)
        index = 0
        if(output):
            for quote in output:
                message = str(quote[0]) + ' (' + str(quote[2]) + ')'
                poll.add_answer(text=message, emoji="✅")
                index += 1
        else:
            await ctx.channel.send("No data found.")
            return

        await ctx.send(poll=poll)