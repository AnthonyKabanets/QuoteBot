from sqlite3 import Connection

#Check for a table, create it if it doesn't exist.
def initTable(con: Connection, tableName):
    cur = con.cursor()
    cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name=':table' ''', {"table": tableName})

    if(cur.fetchone()[0] == 0) : {
        cur.execute('''CREATE TABLE quotes 
                        (id integer NOT NULL PRIMARY KEY, 
                        quote text, 
                        quoteAuthor text NOT NULL, 
                        quoteRecorder text NOT NULL, 
                        date date, 
                        fileExtension text)''')
    }
