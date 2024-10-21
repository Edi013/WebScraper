import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2 import sql

scraped_links_table_name = 'scraped_links3'
to_scrape_links_table_name = 'to_scrap_links'

def scrape_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        # Try to send a request to the URL
        response = requests.get(url, headers=headers, timeout=10)

        # Check if the request was successful
        if response.status_code == 200:
            # Decode with error handling
            content = response.content.decode('utf-8', errors='replace')
            soup = BeautifulSoup(content, 'lxml')

            # Extract all anchor tags with links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Check for both HTTP and HTTPS
                if (href.startswith("http://") or href.startswith("https://") or href.startswith("www")) and '../' not in href:
                    links.append(href)
                else:
                    # Convert relative URL to absolute URL if needed
                    links.append(url + href)

            return links
        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
            return []

    except requests.exceptions.ConnectionError:
        print(f"Error: Failed to connect to {url}. The site may be down.")
        return []

    except requests.exceptions.Timeout:
        print(f"Error: Timeout occurred while trying to reach {url}.")
        return []

    except requests.exceptions.RequestException as e:
        print(f"Error: An error occurred while trying to scrape {url}: {e}")
        return []

    except Exception as e:
        print(f"Unexpected error while scraping {url}: {e}")
        return []

def insert_links(cursor, links, table_name):
    try:
        insert_query = (sql.SQL("INSERT INTO {} (link) VALUES (%s) ON CONFLICT (link) DO NOTHING;")
        .format(sql.Identifier(table_name)))
        cursor.executemany(insert_query, [(link,) for link in links])
    except Exception as e:
        print(f"Error inserting links: {e}")

def get_links(cursor, table_name):
    try:
        select_query = sql.SQL("SELECT link FROM {}").format(sql.Identifier(table_name))
        cursor.execute(select_query)

        links = cursor.fetchall()
        return set([link[1] for link in links])
    except Exception as e:
        print(f"Error getting links: {e}")


if __name__ == "__main__":
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            dbname="WebScrapper",
            user="postgres",
            password="1234",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        print("Connected to the database.")

        to_scrape: set[str] = get_links(cursor, to_scrape_links_table_name)
        #to_scrape.add({'https://about.google/'}) #"http://inf.ucv.ro/"
        scraped_links: set[str] = set()
        while to_scrape:
            current_url = to_scrape.pop()
            result = scrape_page(current_url)

            new_links = set()
            for link in result:
                if link not in scraped_links:
                    to_scrape.add(link)
                    scraped_links.add(link)
                    new_links.add(link)

            if new_links:
                insert_links(cursor, new_links, scraped_links_table_name)
                conn.commit()
                print(f"Inserted {len(new_links)} new links into the database.")

                insert_links(cursor, list(to_scrape), to_scrape_links_table_name)
                conn.commit()
                print(f"Inserted {len(to_scrape)} links able to be scraped into the database.")

            print('To scrape ' + str(len(to_scrape)))
            print('Scrapped '+ str(len(scraped_links)))

        for idx, link in enumerate(scraped_links):
            print(f"{idx + 1}. {link}")
        print("ENDED ------------------")
    except psycopg2.Error as e:
        print(f"Database Error: {e}")
    except Exception as e:
        print(f"Error of unknown type: {e}")
    finally:
        if cursor is not None:
            cursor.close()
            print("Cursor closed.")
        if conn is not None:
            conn.close()
            print("Database connection closed.")