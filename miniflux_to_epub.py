import os
from dotenv import load_dotenv
import miniflux
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import requests
import uuid
import sys
import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

MINIFLUX_URL = os.getenv("MINIFLUX_URL")
MINIFLUX_API_KEY = os.getenv("MINIFLUX_API_KEY")

# print(MINIFLUX_URL)
# sys.exit()

if not MINIFLUX_URL:
    print("Error: MINIFLUX_URL environment variable is not set.")
    exit(1)
if not MINIFLUX_API_KEY:
    print("Error: MINIFLUX_API_KEY environment variable is not set.")
    exit(1)


def create_epub(entry, output_dir="epubs"):
    """Creates an EPUB file from a Miniflux entry."""

    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(entry['title'])
    book.add_author(entry.get('author', 'Unknown'))

    # Fetch the content if it's not already present
    if not entry.get('content'):
        client = miniflux.Client(MINIFLUX_URL.rstrip('/v1'), api_key=MINIFLUX_API_KEY)
        url = f"{MINIFLUX_URL}/v1/entries/{entry['id']}"
        logging.debug(f"Fetching entry content from URL: {url}")
        entry = client.get_entry(url=url)

    # Sanitize HTML content
    soup = BeautifulSoup(entry['content'], 'html.parser')
    for tag in soup.find_all(['script', 'style']):
        tag.decompose()
    sanitized_content = str(soup)

    # Create chapter
    chapter = epub.EpubHtml(title=entry['title'], file_name='chapter.xhtml', lang='en')
    chapter.content = f'<h1>{entry["title"]}</h1>{sanitized_content}'
    book.add_item(chapter)
    book.spine = [chapter]

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Write the EPUB file
    output_path = os.path.join(output_dir, f"{entry['id']}_{entry['title'].replace(' ', '_')}.epub")
    epub.write_epub(output_path, book, {})
    print(f"Created EPUB: {output_path}")


def main():
    """Main function to fetch unread entries and create EPUBs."""
    client = miniflux.Client(MINIFLUX_URL.rstrip('/v1'), api_key=MINIFLUX_API_KEY)

    url = f"{MINIFLUX_URL}/v1/entries"
    logging.debug(f"Fetching entries from URL: {url}")
    try:
        entries = client.get_entries(url=url, status="unread")
    except miniflux.ResourceNotFound as e:
        logging.error(f"Error fetching entries: {e}")
        return

    if entries and entries["entries"]:
        for entry in entries["entries"]:
            create_epub(entry)
    else:
        print("No unread entries found.")


if __name__ == "__main__":
    main()
