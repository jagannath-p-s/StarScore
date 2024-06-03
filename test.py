from bs4 import BeautifulSoup
import re
import requests

def extract_review_count(html_snippet):
    # Parse the HTML
    soup = BeautifulSoup(html_snippet, 'html.parser')
    
    # Find all span tags
    span_tags = soup.find_all('span')
    
    # Iterate through the span tags and look for the one with the review count
    for span in span_tags:
        if span.get('aria-label') and re.search(r'\d+(?:,\d+)* reviews', span['aria-label']):
            review_count = re.search(r'\d+(?:,\d+)*', span['aria-label']).group().replace(',', '')
            return int(review_count)
    return None

def fetch_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None

# Example usage with a Google Maps URL
url = 'https://www.google.com/maps/place/WHITE+DOG+PET+PARTNER/@10.5230321,76.2061876,17z/data=!4m6!3m5!1s0x3ba7ef92d9604c11:0x965344f52b0d0664!8m2!3d10.5230321!4d76.2061876!16s%2Fg%2F11smrzxzct?entry=ttu'
html_content = fetch_html(url)
if html_content:
    review_count = extract_review_count(html_content)
    if review_count is not None:
        print(f"Total number of reviews from URL: {review_count}")
    else:
        print("Review count not found in the HTML content.")
else:
    print("Failed to retrieve HTML content.")
