import asyncio
import sys
import json
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
import random

visited_urls = set()
discovered_urls = set()
response_headers = {}  # Store header names and a single value
url_queue = asyncio.Queue()

# Global variables to control the script's behavior
silent_mode = '--silent' in sys.argv
max_requests = None
output_file = None  # Variable to store the output file path

# List of header names to ignore
ignored_headers = [
    "content-length", "age", "date", "etag", 
    "last-modified", "expires", "keep-alive"
]

# User Agents to rotate
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

def debug_print(message):
    """
    Prints debug messages if not in silent mode.
    
    Args:
        message (str): The debug message to print.
    """
    if not silent_mode:
        print(f"[DEBUG] {message}")

def is_html_page(url):
    """
    Determines if a URL likely points to an HTML page by checking its extension.
    
    Args:
        url (str): The URL to check.
    
    Returns:
        bool: True if the URL is likely an HTML page, False otherwise.
    """
    extensions_to_ignore = ['.js', '.css', '.json']
    return not any(ext in url for ext in extensions_to_ignore)

async def extract_links(page, base_url):
    """
    Extracts all links from a page, including <a> tags, script sources, and CSS links.
    
    Args:
        page (playwright.async_api.Page): The Playwright page object.
        base_url (str): The base URL for resolving relative links.
    
    Returns:
        set: A set of absolute URLs found on the page.
    """
    links = set()
    try:
        elements = await page.query_selector_all("a[href], script[src], link[rel=stylesheet]")
        for element in elements:
            link = await element.get_attribute("href") or await element.get_attribute("src")
            if link:
                abs_url = urljoin(base_url, link)
                if abs_url not in visited_urls:
                    links.add(abs_url)
    except Exception as e:
        debug_print(f"Error extracting links from {base_url}: {e}")
    return links

async def handle_response(response):
    """
    Handles HTTP responses by extracting and storing headers, excluding specified ones.
    
    Args:
        response (playwright.async_api.Response): The Playwright response object.
    """
    headers = response.headers
    for header, value in headers.items():
        # Only add headers that are not in the ignored_headers list
        if header.lower() not in ignored_headers:
            # Store only one value per header
            response_headers[header] = value

async def crawl_page(browser, url):
    """
    Crawls a page by visiting the URL, extracting links, and queuing new ones for crawling.
    
    Args:
        browser (playwright.async_api.Browser): The Playwright browser object.
        url (str): The URL of the page to crawl.
    """
    if url in visited_urls or (max_requests and len(visited_urls) >= max_requests):
        return
    visited_urls.add(url)
    debug_print(f"Crawling: {url}")
    
    user_agent = random.choice(user_agents)
    
    context = await browser.new_context(user_agent=user_agent)
    page = await context.new_page()
    page.on('response', handle_response)
    
    try:
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

        new_links = await extract_links(page, url)
        for link in new_links:
            parsed_url = urlparse(link)
            if parsed_url.netloc == urlparse(url).netloc:
                if link not in visited_urls and (not max_requests or len(visited_urls) < max_requests):
                    await url_queue.put(link)
                    if is_html_page(link):
                        discovered_urls.add(link)
    except Exception as e:
        debug_print(f"Error crawling {url}: {e}")
    finally:
        await page.close()

async def worker(browser):
    """
    Worker function that continuously fetches URLs from the queue and processes them.
    
    Args:
        browser (playwright.async_api.Browser): The Playwright browser object.
    """
    while True:
        url = await url_queue.get()
        if url is None:  # Sentinel value to stop the worker
            url_queue.task_done()
            break
        await crawl_page(browser, url)
        url_queue.task_done()

async def main(start_url, max_requests):
    """
    Main function that initializes the browser, starts workers, and manages the crawling process.
    
    Args:
        start_url (str): The starting URL for the crawl.
        max_requests (int): The maximum number of requests to make.
    
    Returns:
        tuple: (set of discovered URLs, dictionary of unique response headers)
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        await url_queue.put(start_url)
        
        tasks = []
        for _ in range(10):  # Using 10 workers
            task = asyncio.create_task(worker(browser))
            tasks.append(task)

        await url_queue.join()
        for task in tasks:
            task.cancel()

        await browser.close()

        return discovered_urls, response_headers

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python nightcrawler.py <start_url> [--silent] [--max-requests <number>] [--output-file <file_path>]")
        sys.exit(1)

    start_url = sys.argv[1]

    # Parse the --max-requests argument if provided
    if '--max-requests' in sys.argv:
        try:
            max_requests_index = sys.argv.index('--max-requests') + 1
            max_requests = int(sys.argv[max_requests_index])
        except (IndexError, ValueError):
            print("Error: Invalid value for --max-requests")
            sys.exit(1)

    # Parse the --output-file argument if provided
    if '--output-file' in sys.argv:
        try:
            output_file_index = sys.argv.index('--output-file') + 1
            output_file = sys.argv[output_file_index]
        except (IndexError):
            print("Error: Missing value for --output-file")
            sys.exit(1)

    urls, headers = asyncio.run(main(start_url, max_requests))

    # Clean up headers to ensure only one value per header name
    headers = {header: value for header, value in response_headers.items()}

    # Prepare JSON output
    output = {
        "urls": list(urls),
        "headers": headers
    }

    # Write JSON output to file or print to stdout
    if output_file:
        with open(output_file, 'w') as file:
            json.dump(output, file, indent=4)
        if not silent_mode:
            print(f"Results written to {output_file}")
    else:
        print(json.dumps(output, indent=4))

