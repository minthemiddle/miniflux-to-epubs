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
import argparse

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

    # Download and embed images
    for picture_tag in soup.find_all('picture'):
        img_tag = picture_tag.find('img')
        if img_tag:
            img_url = img_tag['src']
            try:
                logging.debug(f"Downloading image from: {img_url}")
                img_data = requests.get(img_url, stream=True)
                img_data.raise_for_status()
                img_content = img_data.content
                img_extension = os.path.splitext(img_url)[1][1:]
                if not img_extension:
                    img_extension = "jpeg"  # default to jpeg if no extension
                img_name = f"img_{uuid.uuid4()}.{img_extension}"

                epub_img = epub.EpubImage(uid=img_name, file_name=img_name, content=img_content)
                book.add_item(epub_img)
                img_tag['src'] = img_name
                logging.debug(f"Embedded image: {img_name}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Error downloading image from {img_url}: {e}")
                picture_tag.decompose()  # remove the picture tag if we can't download it
                continue
        else:
            # If no img tag is found, try to find source tags
            for source_tag in picture_tag.find_all('source'):
                srcset = source_tag.get('srcset')
                if srcset:
                    # Take the first URL from srcset
                    img_url = srcset.split(',')[0].split()[0]
                    try:
                        logging.debug(f"Downloading image from: {img_url}")
                        img_data = requests.get(img_url, stream=True)
                        img_data.raise_for_status()
                        img_content = img_data.content
                        img_extension = os.path.splitext(img_url)[1][1:]
                        if not img_extension:
                            img_extension = "jpeg"  # default to jpeg if no extension
                        img_name = f"img_{uuid.uuid4()}.{img_extension}"

                        epub_img = epub.EpubImage(uid=img_name, file_name=img_name, content=img_content)
                        book.add_item(epub_img)
                        source_tag['src'] = img_name
                        logging.debug(f"Embedded image: {img_name}")
                    except requests.exceptions.RequestException as e:
                        logging.error(f"Error downloading image from {img_url}: {e}")
                        source_tag.decompose()  # remove the source tag if we can't download it
                        continue
                else:
                    source_tag.decompose()  # remove the source tag if no srcset is found
            except requests.exceptions.RequestException as e:
                logging.error(f"Error downloading image from {img_url}: {e}")
                picture_tag.decompose()  # remove the picture tag if we can't download it
                continue

    for img_tag in soup.find_all('img'):
        if not img_tag.has_attr('src'):
            continue
        img_url = img_tag['src']
        if img_url:
            try:
                logging.debug(f"Downloading image from: {img_url}")
                img_data = requests.get(img_url, stream=True)
                img_data.raise_for_status()
                img_content = img_data.content
                img_extension = os.path.splitext(img_url)[1][1:]
                if not img_extension:
                    img_extension = "jpeg"  # default to jpeg if no extension
                img_name = f"img_{uuid.uuid4()}.{img_extension}"

            epub_img = epub.EpubImage(uid=img_name, file_name=img_name, content=img_content)
            book.add_item(epub_img)
            img_tag['src'] = img_name
            logging.debug(f"Embedded image: {img_name}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading image from {img_url}: {e}")
            img_tag.decompose()  # remove the tag if we can't download it
            continue

    sanitized_content = str(soup)

    # Create chapter
    chapter = epub.EpubHtml(title=entry['title'], file_name='chapter.xhtml', lang='en')
    chapter.content = f'<h1>{entry["title"]}</h1>{sanitized_content}'
    book.add_item(chapter)
    book.toc = (chapter, )
    book.spine = ['nav', chapter]

    # Add navigation files (NCX and OPF)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Write the EPUB file
    output_path = os.path.join(output_dir, f"{entry['id']}_{entry['title'].replace(' ', '_')}.epub")
    epub.write_epub(output_path, book, {})
    print(f"Created EPUB: {output_path}")


def main():
    """Main function to fetch unread entries and create EPUBs."""
    parser = argparse.ArgumentParser(description="Fetch unread entries from Miniflux and create EPUBs.")
    parser.add_argument("--limit", type=int, help="Limit the number of entries to process.")
    args = parser.parse_args()

    client = miniflux.Client(MINIFLUX_URL.rstrip('/v1'), api_key=MINIFLUX_API_KEY)

    url = f"{MINIFLUX_URL}/v1/entries"
    logging.debug(f"Fetching entries from URL: {url}")
    try:
        entries = client.get_entries(url=url, status="unread")
    except miniflux.ResourceNotFound as e:
        logging.error(f"Error fetching entries: {e}")
        return

    if entries and entries["entries"]:
        if args.limit:
            limited_entries = entries["entries"][:args.limit]
        else:
            limited_entries = entries["entries"]
        for entry in limited_entries:
            create_epub(entry)
    else:
        print("No unread entries found.")


if __name__ == "__main__":
    main()
