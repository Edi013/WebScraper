# Web Scraper

## Project Objective
This script is designed to scrape web pages using Chrome for URLs and store the data in a PostgreSQL database.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Database Setup](#database-setup)
- [Usage](#usage)
- [Stopping the Program](#stopping-the-program)

## Features
- **Web scraping**: Scrapes web pages for all non-archive URLs.
- **Database Integration**: Stores scraped, target, and unreachable URLs in a PostgreSQL database.
- **Multi-process Execution**: Utilizes multiple processes, with multiple scrapers.
- **Keyboard-initiated Exit**: Allows graceful program termination with the "ESC" key and can ensure database state consistency if chosen.
- **Error Handling**

## Requirements
- **Python 3.x**
- **Libraries**: 
  - `requests`
  - `BeautifulSoup4`
  - `psycopg2`
  - `keyboard`
  - You can install all of them with one command:  
    ```bash
    pip install requests beautifulsoup4 psycopg2 keyboard
    ```
- **PostgreSQL DB**

## Database Setup
Create a PostgreSQL database with the following tables:

- `result_links`: Stores successfully scraped URLs.
- `target_links`: Contains URLs targeted for scraping.
- `unreached_links`: Logs URLs that were unreachable.

SQL to create these tables:
```sql
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


## Usage
1. **Install dependencies**: Make sure you have all required libraries installed. Use the following command:
   ```bash
   pip install requests beautifulsoup4 psycopg2 keyboard
2. **Set up the database and configure the connection**.
3. **Run the script and enjoy.**

