import requests
from bs4 import BeautifulSoup


def scrape_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        # Try to send a request to the URL
        response = requests.get(url, headers=headers, timeout=10)  # Set a timeout of 10 seconds

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
                if href.startswith("http://") or href.startswith("https://") or href.startswith("www"):
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


# Example usage
if __name__ == "__main__":

    urls_reached = []
    to_scrape: set[str] = {"http://inf.ucv.ro/"}
    scraped_links: set[str] = set()
    while to_scrape:
        current_url = to_scrape.pop()
        result = scrape_page(current_url)

        for link in result:
            if link not in urls_reached:
                to_scrape.add(link)
            scraped_links.add(link)

        print('Already reached ' + str(len(urls_reached)))
        print('To scrape ' + str(len(to_scrape)))
        print('Scrapped '+ str(len(scraped_links)))

    for idx, link in enumerate(scraped_links):
        print(f"{idx + 1}. {link}")
    print("ENDED ------------------")
