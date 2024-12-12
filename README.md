# Miniflux to EPUB Converter

This script fetches unread entries from a Miniflux instance and converts them into EPUB files.

## Prerequisites

-   Python 3.6+
-   A Miniflux instance
-   A Miniflux API key

## Installation

1.  Clone the repository:

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

3.  Create a `.env` file in the root directory and add your Miniflux URL and API key:

    ```
    MINIFLUX_URL="https://your-miniflux-instance.com"
    MINIFLUX_API_KEY="your_api_key"
    ```

## Usage

Run the script:

```bash
python miniflux_to_epub.py
```

The script will fetch all unread entries from your Miniflux instance and create an EPUB file for each entry in the `epubs` directory.

## Logging

The script uses the `logging` module to provide detailed output. By default, it logs debug messages to the console.

## Dependencies

-   `miniflux`: A Python client for the Miniflux API.
-   `ebooklib`: A Python library for creating EPUB files.
-   `python-dotenv`: A Python library for loading environment variables from a `.env` file.
-   `requests`: A Python library for making HTTP requests.
-   `beautifulsoup4`: A Python library for parsing HTML and XML.
