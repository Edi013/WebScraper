import multiprocessing
import os

import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2 import sql
import keyboard
from collections.abc import Iterable

result_links_table_name = 'result_links'
target_links_table_name = 'target_links'
unreached_links_table_name = 'unreached_links'
initial_link = 'http://inf.ucv.ro/'

correctlyStoppedMessage = "The program stopped correctly with 1/1 required actions."
exit_initiated = False
FAST_EXIT = True

def scrape_page(url, db_cursor, conn):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    archive_extensions = ('.zip', '.tar.gz', '.tar', '.gz', '.rar', '.7z')

    try:
        if url.endswith(archive_extensions):
            print(f"Skipping archive file: {url}")
            return []  # Skip the processing for this URL

        response = requests.get(url, headers=headers, timeout=1)
        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='replace')

            content_type = response.headers.get('Content-Type', '').lower()
            if 'xml' in content_type or 'xhtml' in content_type or content.strip().startswith('<?xml'):
                soup = BeautifulSoup(content, features="xml")
            else:
                soup = BeautifulSoup(content, 'lxml')

            links = []
            for tag in soup.find_all('a', href=True):
                href = tag['href']
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
        handle_unreached_link(db_cursor, url, conn)
        return []

    except requests.exceptions.Timeout:
        print(f"Error: Timeout occurred while trying to reach {url}.")
        handle_unreached_link(db_cursor, url, conn)
        return []

    except requests.exceptions.RequestException as e:
        print(f"Error: An error occurred while trying to scrape {url}: {e}")
        return []

    except Exception as e:
        print(f"Unexpected error while scraping {url}: {e}")
        return []

def insert_links(cursor, links, table_name):
    try:
        if isinstance(links, str):
            links = [links]

        if not isinstance(links, Iterable):
            raise TypeError("Inserting supports only iterable types.")

        insert_query = (sql.SQL("INSERT INTO {} (link) VALUES (%s) ON CONFLICT (link) DO NOTHING;")
                        .format(sql.Identifier(table_name)))
        cursor.executemany(insert_query, [(link,) for link in links])
    except (TypeError, Exception) as e:
        print(f"Error inserting links: {e}")
    finally:
        return cursor.rowcount

def get_links(cursor, table_name):
    try:
        select_query = sql.SQL("SELECT link FROM {}").format(sql.Identifier(table_name))
        cursor.execute(select_query)

        links = cursor.fetchall()
        return set([link[0] for link in links])
    except Exception as e:
        print(f"Error getting links: {e}")

def delete_links(cursor, links, table_name):
    try:
        if isinstance(links, str):
            delete_query = sql.SQL("DELETE FROM {} WHERE link = %s;").format(
                sql.Identifier(table_name)
            )
            cursor.execute(delete_query, (links,))
            return cursor.rowcount > 0

        if not isinstance(links, Iterable):
            raise TypeError("Inserting supports only iterable types.")

        delete_query = sql.SQL("DELETE FROM {} WHERE link IN ({});").format(
            sql.Identifier(table_name),
            sql.SQL(',').join(sql.Placeholder() * len(links))
        )
        cursor.executemany(delete_query, links)

    except (TypeError, Exception) as e:
        print(f"Error deleting links: {e}")
    finally:
        return cursor.rowcount

def connect_to_postgresql():
    conn = psycopg2.connect(
        dbname="ScraperDb",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )
    print("Connected to the database.")
    return conn

def handle_unreached_link(cursor, current_url, conn):
    if insert_links(cursor, current_url, unreached_links_table_name):
        conn.commit()
        print(f"Unreached url stored: {current_url}")

def initiate_exit(cursor, target_links, conn):
    global exit_initiated, FAST_EXIT
    exit_initiated = True
    print("ESC key pressed. Stopping the program...")
    if not FAST_EXIT:
        affected_rows = insert_links(cursor, target_links, target_links_table_name)
        if affected_rows:
            conn.commit()
        print(f"In memory links list synchronized with db. Rows added: {affected_rows}, links number: {len(target_links)}.")

def scraping_process():
    conn = None
    cursor = None
    target_links: set[str] = set()
    try:
        conn = connect_to_postgresql()
        cursor = conn.cursor()
        target_links = get_links(cursor, target_links_table_name)
        target_links.add(initial_link) if len(target_links) == 0 else None

        while target_links and not exit_initiated:
            pid = os.getpid()
            print(f"Process ID: {pid}")
            current_url = target_links.pop()
            print(f"Scrapping current url: {current_url}")
            result = scrape_page(current_url, cursor, conn)

            new_links_scraped = set()
            for link in result:
                if link not in target_links:
                    target_links.add(link)
                    new_links_scraped.add(link)

            if new_links_scraped:
                insert_links(cursor, new_links_scraped, result_links_table_name)
                insert_links(cursor, new_links_scraped, target_links_table_name)
            print('New scrapped links: ' + str(len(new_links_scraped)))

            if delete_links(cursor, current_url, target_links_table_name):
                print(f"Deleted scraped url completed: {current_url}")
            conn.commit()

            if keyboard.is_pressed('esc'):
                initiate_exit(cursor, target_links, conn)
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

        print(f"Program stopped correctly: {exit_initiated}")
        if exit_initiated:
            print(correctlyStoppedMessage)
        print("---Scraper process ended---")

if __name__ == "__main__":
    num_processes = 2
    processes = []

    for _ in range(num_processes):
        process = multiprocessing.Process(target=scraping_process)
        process.start()
        processes.append(process)

    for process in processes:
        process.join()  # Wait for all processes to complete

    print("All processes have completed.")