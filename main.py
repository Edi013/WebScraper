import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2 import sql
import keyboard


scraped_links_table_name = 'scraped_links3'
to_scrape_links_table_name = 'to_scrap_links'


def scrape_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        # Try to send a request to the URL
        response = requests.get(url, headers=headers, timeout=1)

        # Check if the request was successful
        if response.status_code == 200:
            # Decode with error handling
            content = response.content.decode('utf-8', errors='replace')

            content_type = response.headers.get('Content-Type', '')
            if 'xml' in content_type or 'xhtml' in content_type:
                soup = BeautifulSoup(content, features="xml")  # Use XML parser
            else:
                soup = BeautifulSoup(content, 'lxml')

            # Extract all anchor tags with links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if (href.startswith("http://") or href.startswith("https://") or href.startswith("www")) and '../' not in href\
                        and '..' not in href and (href.count('.com') < 1):
                    links.append(href)
                else:
                    #print(f"This link is not included: {link}")
                    continue

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
        return set([link[0] for link in links])
    except Exception as e:
        print(f"Error getting links: {e}")

def delete_to_scrape_links(cursor, links, table_name):
    try:
        delete_query = sql.SQL("DELETE FROM {} WHERE link IN ({});").format(
            sql.Identifier(table_name),
            sql.SQL(',').join(sql.Placeholder() * len(links))
        )

        cursor.execute(delete_query, links)
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting links: {e}")

def delete_to_scrape_link(cursor, link, table_name):
    try:
        delete_query = sql.SQL("DELETE FROM {} WHERE link = %s;").format(
            sql.Identifier(table_name)
        )
        cursor.execute(delete_query, (link,))

        if cursor.rowcount > 0:
            print(f"Successfully deleted link: {link}")
            return True
        else:
            print(f"No link found to delete: {link}")
            return False
    except Exception as e:
        print(f"Error deleting link: {e}")
        return False


if __name__ == "__main__":
    conn = None
    cursor = None
    to_scrape: set[str] = set()
    scraped_links_to_delete_from_database: list = []
    scraped_links: set[str] = set()
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

        to_scrape = get_links(cursor, to_scrape_links_table_name)
        while to_scrape:
            if keyboard.is_pressed('esc'):
                print("ESC key pressed. Stopping the program...")
                insert_links(cursor, list(to_scrape), to_scrape_links_table_name)
                conn.commit()
                print(f"Inserted {len(to_scrape)} links able to be scraped into the database.")
                print("The program stopped correctly 1/1.")
                # delete_result = delete_to_scrape_links(cursor, scraped_links_to_delete_from_database, to_scrape_links_table_name)
                # conn.commit()
                # print('Deleted used rows from retrieved ones. ' + "The program stopped correctly 2/2." ) if delete_result else print('NOT deleted used rows from retrieved ones.' + "The program didn't stop correctly 2nd/2 step.")
                break

            current_url = to_scrape.pop()
            # scraped_links_to_delete_from_database.append(current_url)
            result = scrape_page(current_url)

            new_links_scraped = set()
            for link in result:
                if link not in scraped_links and link not in to_scrape:
                    to_scrape.add(link)
                    scraped_links.add(link)
                    new_links_scraped.add(link)

            if new_links_scraped:
                insert_links(cursor, new_links_scraped, scraped_links_table_name)
                conn.commit()
                print(f"Inserted {len(new_links_scraped)} scraped links into the database.")

                insert_links(cursor, list(to_scrape), to_scrape_links_table_name)
                conn.commit()
                print(f"Inserted {len(to_scrape)} links able to be scraped into the database.")

            print('To scrape ' + str(len(to_scrape)))
            print('Scrapped '+ str(len(scraped_links)))

            delete_to_scrape_link(cursor, current_url, to_scrape_links_table_name)
            conn.commit()
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