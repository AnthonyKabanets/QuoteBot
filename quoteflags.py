from discord.ext import commands
import math

class QuoteFlags(commands.FlagConverter):
    idMin: int = 0
    idMax: int = math.inf
    dateStart: str = "0001/01/01"
    dateEnd: str = "9999/12/31"
    dateFormat: str = '%Y/%m/%d'

class AddFlags(commands.FlagConverter):
    id: int = -1