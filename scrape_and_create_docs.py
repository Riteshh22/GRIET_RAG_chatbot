import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urlparse

BASE_URL = "https://www.griet.ac.in"
DOCS_DIR = "griet_docs"
os.makedirs(DOCS_DIR, exist_ok=True)

def scrape_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted tags
        for element in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
            element.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)
        
        # Save file
        filename = url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_") + ".txt"
        filepath = os.path.join(DOCS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Source URL: {url}\n\n")
            f.write(clean_text)
        
        print(f"✅ Scraped: {url}")
        return clean_text
    except Exception as e:
        print(f"❌ Failed {url}: {e}")
        return ""

def main():
    print("🚀 Starting GRIET Website Scraper...\n")
    
    key_pages = [
        "https://www.griet.ac.in/",
        "https://www.griet.ac.in/about.php",
        "https://www.griet.ac.in/admissions.php",
        "https://www.griet.ac.in/programmes.php",
        "https://www.griet.ac.in/departments.php",
        "https://www.griet.ac.in/placements.php",
        "https://www.griet.ac.in/contactus.php",
        "https://www.griet.ac.in/rankings_recognitions.php",
        "https://www.griet.ac.in/facilities.php",
        "https://www.griet.ac.in/mandatory_disclosures.php",
    ]
    
    for page in key_pages:
        scrape_page(page)
        time.sleep(1.5)
    
    print(f"\n✅ Scraping completed! Documents saved in '{DOCS_DIR}/' folder.")

if __name__ == "__main__":
    main()