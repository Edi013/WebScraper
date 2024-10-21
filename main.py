import requests
from bs4 import BeautifulSoup


# Function to scrape the webpage and extract all links
def scrape_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract all anchor tags with links
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith("http") or href.startswith("www"):
                links.append(href)
            else:
                # Convert relative URL to absolute URL if needed
                links.append(url + href)

        return links
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return []


# Example usage
if __name__ == "__main__":

    urls = ["http://inf.ucv.ro/"]
    scraped_links = urls
    while len(urls) != 0:
        result = scrape_page(urls[0])
        for link in result:
            if link not in scraped_links:
                scraped_links.append(link)
            if link not in urls:
                urls.append(link)
        urls.remove(urls[0])
        print(urls)
        print('Scrapped '+ str(len(scraped_links)))

    for idx, link in enumerate(scraped_links):
        print(f"{idx + 1}. {link}")
    print("ENDED ------------------")
