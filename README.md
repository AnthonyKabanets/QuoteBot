# QuoteBot
A simple Discord bot using Python and SQLite3, for recording quotes.

Commands


$quotedCount username

Outputs the amount of times a user has been quoted.


$quoterCount username


Outputs the amount of times a user has added quotes.


$totalQuotes

Outputs the total amount of quotes saved.


$idQuote number

Outputs a quote with the specified unique ID.


$quote username [quote] [attachment]

If neither quote or attachment are included, this will output a random quote from username.

If either quote or attachment are included, this will save a new quote with that quote and attachment.
