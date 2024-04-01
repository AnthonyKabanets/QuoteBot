import sqlite3

aliasDB = "aliases.db"
con = sqlite3.connect(aliasDB)
cur = con.cursor()

#Check if table exists, if it doesn't create it.
cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='alias' ''')
if(cur.fetchone()[0] == 0) : {
    cur.execute('''CREATE TABLE alias
                    (inputName text NOT NULL, 
                    outputName text NOT NULL)''')
}

#Will return a matching alias for this name. 
#If no alias exists, will return the provided name.
def fetchAlias(name):
    print("Checking " + name + " for an alias")
    cur.execute("SELECT outputName FROM alias WHERE inputName=:name ", {"name": name})
    output = cur.fetchone()
    if output is None: #No rows matching name found.
        return name 
    
    return output[0]

#Returns a (Bool, String) tuple. 
#If the alias already exists, returns (False, existingOutputName)
#If successfully created, returns (True, outputName)
def addAlias(inputName, outputName):
    cur.execute("SELECT inputName, outputName FROM alias WHERE inputName=:name ", {"name": inputName})

    output = cur.fetchone()
    if output is not None: #Alias already exists for this inputName
        return (False, output[1])
     
    cur.execute("INSERT INTO alias(inputName, outputName) VALUES (?,?)", (inputName, outputName))
    con.commit()
    return (True, outputName)