from xmlrpc.client import boolean

import requests
from bs4 import BeautifulSoup
import psycopg2
# from lxml.xslt import message
from psycopg2 import sql
import keyboard


result_links_table_name = 'result_links'
target_links_table_name = 'target_links'
correctlyStoppedMessage = "The program stopped correctly with 1/1 required actions."
correctlySoppedValue = False

def scrape_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=1)

        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='replace')

            content_type = response.headers.get('Content-Type', '').lower()
            if 'xml' in content_type or 'xhtml' in content_type or content.strip().startswith('<?xml'):
                soup = BeautifulSoup(content, features="xml")
            else:
                soup = BeautifulSoup(content, 'lxml')

            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if (href.startswith("http://") or href.startswith("https://") or href.startswith("www")) and '../' not in href\
                        and '..' not in href and (href.count('.com') < 1):
                    links.append(href)
                else:
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

# generic method to insert data into a table within given table architecture constraints : contanins link column.
def insert_links(cursor, links, table_name):
    try:
        insert_query = (sql.SQL("INSERT INTO {} (link) VALUES (%s) ON CONFLICT (link) DO NOTHING;")
        .format(sql.Identifier(table_name)))
        cursor.executemany(insert_query, [(link,) for link in links])
    except Exception as e:
        print(f"Error inserting links: {e}")

# generic method to get data into a table within given table architecture constraints : contanins link column.
def get_links(cursor, table_name):
    try:
        select_query = sql.SQL("SELECT link FROM {}").format(sql.Identifier(table_name))
        cursor.execute(select_query)

        links = cursor.fetchall()
        return set([link[0] for link in links])
    except Exception as e:
        print(f"Error getting links: {e}")

# generic method to delete data into a table within given table architecture constraints : contanins link column.
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

# generic method to delete data into a table within given table architecture constraints : contanins link column.
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

def connect_to_postgresql():
    conn = psycopg2.connect(
        dbname="WebScrapper",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )
    print("Connected to the database.")
    return conn

if __name__ == "__main__":
    conn = None
    cursor = None
    target_links: set[str] = set()
    try:
        conn = connect_to_postgresql()
        cursor = conn.cursor()

        target_links = get_links(cursor, target_links_table_name)
        while target_links:
            if keyboard.is_pressed('esc'):
                print("ESC key pressed. Stopping the program...")
                insert_links(cursor, list(target_links), target_links_table_name)
                conn.commit()
                print(f"In memory links list syncronized with db, links number: {len(target_links)}.")
                correctlySoppedValue = True
                break

            current_url = target_links.pop()
            print(f"Scrapping current url: {current_url}")
            result = scrape_page(current_url)

            new_links_scraped = set()
            for link in result:
                if link not in target_links:
                    target_links.add(link)
                    new_links_scraped.add(link)

            if new_links_scraped:
                insert_links(cursor, new_links_scraped, result_links_table_name)
                insert_links(cursor, new_links_scraped, target_links_table_name)
                delete_to_scrape_link(cursor, current_url, target_links_table_name)
                conn.commit()
                print(f"Inserted {len(new_links_scraped)} scraped links into the database ( both in target column and scrapped column.")
                print(f"Deleted scraped url: {current_url}")
                current_url = ""

            print('New scrapped links: '+ str(len(new_links_scraped)))
            print('Total amount of target links available: ' + str(len(target_links)))
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

        print("Prgoram stopped correctly: " + correctlySoppedValue)
        if(correctlySoppedValue):
            print(correctlyStoppedMessage)

# trebuie sa gestionam daca link ul intra pe timeout, trb sters sau nu ?