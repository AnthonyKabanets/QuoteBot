from sqlite3 import Connection

#Check for a table, create it if it doesn't exist.
def initTable(con: Connection):
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS "quote" 
                    (id integer NOT NULL PRIMARY KEY, 
                    quote text, 
                    quoteRecorder text NOT NULL, 
                    date date)''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS "authors" (
                    id integer NOT NULL,
                    author text NOT NULL)''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS "attachments" (
                "id"	INTEGER NOT NULL,
                "fileIndex"	TEXT,
                "extension"	TEXT NOT NULL)''')
    cur.close()
    con.commit()

from ruamel.yaml import YAML
with open("config.yaml", "r", encoding = "utf-8") as file: #utf-8 as standard
    yaml = YAML()
    config = yaml.load(file)
def getConfigFile():
    return config
def getConfig(key):
    return config[key]

import constants
import mimetypes
class QuoteHelpers:
    def idAlreadyUsed(con, id):
        cur = con.cursor()
        cur.execute("SELECT count(authors.id) FROM authors WHERE authors.id = :id", {"id": id})
        count = cur.fetchone()[0]
        cur.close()
        return count > 0

    async def insertQuote(ctx, con, authorList, quote, today, id = -1):
        cur = con.cursor()       
        if id != -1:
            cur.execute("INSERT INTO quotes(quote, quoteRecorder, date, id) VALUES (?, ?, ?, ?)", (quote, ctx.author.name, today, id))
        else: 
            cur.execute("INSERT INTO quotes(quote, quoteRecorder, date) VALUES (?, ?, ?)", (quote, ctx.author.name, today))
            id = cur.execute("SELECT last_insert_rowid()").fetchone()[0]

        for author in authorList:
            cur.execute("INSERT INTO authors(id, author) VALUES (?, ?)", (id, author))
        
        if ctx.message.attachments:
            res = await QuoteHelpers.parseAttachments(ctx, id, con)
            if res == -1:
                con.rollback()
                return -1
        
        cur.close()
        return id
    
    #parseAttachments will not commit changes to DB, user should do so.
    #This should be changed to return a list of attachments that can be saved immediately.
    async def parseAttachments(ctx, quoteID, con):
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
            cursor = con.cursor()
            cursor.execute("INSERT INTO attachments(id, fileIndex, extension) VALUES (?, ?, ?)", row)
            cursor.close()
            index += 1
            
            await attachment.save(getConfig("Attachments") + fileName)
    
    def genQuoteString(quote: str, authors: str, date: str, id: int):
        return str(quote or '') + '\n-# -' + authors + ', ' + date + ", ID: " + str(id)     

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

    def genAttachmentStrings(con, id):
        cur = con.cursor()
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