# QuoteBot
A simple Discord bot using Python and SQLite3, for recording quotes.

Quotes are saved in a .db file. The name of this file can be set in config.json

The directory attachments are saved in can be set in config.json


Commands

$quotedCount [username]

Outputs the amount of times a user has been quoted.

$quoteRank [number]

Outputs the first [number] of people with the most quotes, as well as how many quotes each of those people have attributed to them.

$quoterCount username


Outputs the amount of times a user has added quotes.


$totalQuotes

Outputs the total amount of quotes saved.


$idQuote [number]

Outputs a quote with the specified unique ID.


$quote username [quote] [attachment]

If neither quote or attachment are included, this will output a random quote from username.

If either quote or attachment are included, this will save a new quote with that quote and attachment.

$deleteQuote id

Deletes a quote with the chosen id. Deletes saved attachments as well.

Requires a role to use. Required role is set in config.json
