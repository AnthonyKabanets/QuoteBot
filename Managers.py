import sqlite3
import Printer
import admin
import alias

printManager = None
aliasManager = None
adminManager = None
def initManagers(bot, con: sqlite3.Connection):
    global aliasManager 
    aliasManager = alias.Alias(bot)
    global printManager 
    printManager = Printer.Print(bot, con)
    global adminManager 
    adminManager = admin.Admin(bot, con, printManager=printManager)