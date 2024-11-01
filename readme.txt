Web Scraper 


Project Objective : This script is designed to scrape web pages for URLs and store the data in a PostgreSQL database.


Table of Contents
Features
Requirements
Database Setup
Usage
Stopping the Program


Features
- Web scraping: Scrapes web pages for all non-archive URLs.
- Database Integration: Stores scraped, target, and unreachable URLs in a PostgreSQL database.
- Multi-process Execution: It utilizes multiple processes, multiple scrapers.
- Keyboard-initiated Exit: Allows graceful program termination with the "ESC" key, can ensure database state consistency if chosen.
- Error Handling.


Requirements
- Python 3.x
- Libraries: 
	-- requests
	-- BeautifulSoup4
	-- psycopg2
	-- keyboard
	-- you can use this command to install all in one : pip install requests beautifulsoup4 psycopg2 keyboard
- PostgreSQL DB.


Database Setup
Create a PostgreSQL database with the following tables:
- result_links: Stores successfully scraped URLs.
- target_links: Contains URLs targeted for scraping.
- unreached_links: Logs URLs that were unreachable.

SQL to create these tables:
CREATE TABLE result_links (
    id SERIAL PRIMARY KEY,
    link TEXT UNIQUE
);

CREATE TABLE target_links (
    id SERIAL PRIMARY KEY,
    link TEXT UNIQUE
);

CREATE TABLE unreached_links (
    id SERIAL PRIMARY KEY,
    link TEXT UNIQUE
);


Usage
Install dependencies
DB setup and configure the connection.
Run the script and enjoy.


Stopping the Program
To exit the program, hold the "ESC" key untill every process is stopped.
For a quick exit with 99.99% data accuracy, set True in the exit function, for a slower exit with 100% data acuracy, set False.