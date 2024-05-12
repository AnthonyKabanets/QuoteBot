# QuoteBot
A simple Discord bot using Python and SQLite3, for recording quotes.

Quotes are saved in a .db file. The name of this file can be set in config.json

The directory attachments are saved in can be set in config.json


Commands

$quotedCount [username]

Outputs the amount of times a user has been quoted.

$quoteRank [number]

Outputs the first [number] of people with the most quotes, as well as how many quotes each of those people have attributed to them.

$quoterCount [username]

Outputs the amount of times a user has added quotes.


$totalQuotes

Outputs the total amount of quotes saved.


$idQuote [number]

Outputs a quote with the specified unique ID.


$addQuote [name] [quote] [attachment]

Save a quote with that quote and/or attachment. At least one of quote or attachment must be included.

Attachments (smaller than 8 MB) are allowed.


$quote [name] [numQuotes] [flags]

Output a random quote from username. 

numQuotes specifies how many quotes to send. Optional, default is 1. Min is 1, max is 20.

flags: Includes dateStart, dateEnd, dateFormat, idMin, idMax
  Default format for dates is Year/Month/Day. Does not include hours or minutes.

Example: $quote John 2 dateStart:2022/8/1 dateEnd:2022/9/2


$deleteQuote id

Deletes a quote with the chosen id. Deletes saved attachments as well.

Requires a role to use. Required role is set in config file.


$addAlias inputName outputName

Adds an alias to inputName. Any quotes requested or added for inputName will instead be redirected to outputName.

NOTE: This will not change any existing quotes registered to inputName.
