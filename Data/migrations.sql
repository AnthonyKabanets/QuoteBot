CREATE TABLE "authors" (
	"id"	INTEGER NOT NULL,
	"author"	TEXT NOT NULL
);

CREATE TABLE "attachments" (
	"id"	INTEGER NOT NULL,
	"fileIndex"	TEXT,
	"extension"	TEXT NOT NULL
);

INSERT INTO authors (id, author) SELECT id, quoteAuthor FROM quotes;
ALTER TABLE quotes DROP COLUMN quoteAuthor;

INSERT INTO attachments (id, extension) SELECT id, fileExtension FROM quotes WHERE fileExtension NOT NULL;
ALTER TABLE quotes DROP COLUMN fileExtension;
UPDATE attachments SET extension = '.' || extension;

UPDATE quotes SET quoteRecorder = lower(quoteRecorder);