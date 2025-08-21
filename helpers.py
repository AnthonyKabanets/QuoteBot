import sqlite3
from sqlite3 import Connection

#Check for a table, create it if it doesn't exist.
def initTable(con: Connection, tableName):
    cur = con.cursor()
    cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name=:table ''', {"table": tableName})

    if(cur.fetchone()[0] == 0): 
        cur.execute('''CREATE TABLE :table 
                        (id integer NOT NULL PRIMARY KEY, 
                        quote text, 
                        quoteRecorder text NOT NULL, 
                        date date, 
                        fileExtension text)''', {"table": tableName})
        
        cur.execute('''CREATE TABLE "authors" (
	                    id integer NOT NULL,
	                    author text NOT NULL
                    ''')

from ruamel.yaml import YAML
with open("config.yaml", "r", encoding = "utf-8") as file: #utf-8 as standard
    yaml = YAML()
    config = yaml.load(file)
def getConfigFile():
    return config
def getConfig(key):
    return config[key]