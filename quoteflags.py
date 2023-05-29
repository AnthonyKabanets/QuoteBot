from discord.ext import commands
from datetime import date
import math

class QuoteFlags(commands.FlagConverter):
    idMin: int = 0
    idMax: int = math.inf
    dateStart: str = date.min.strftime("%Y/%m/%d")
    dateEnd: str = date.max.strftime("%Y/%m/%d")
    dateFormat: str = '%Y/%m/%d'