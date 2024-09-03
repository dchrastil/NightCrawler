# NightCrawler

`NightCrawler` is a web crawling script using Playwright that helps discover and list all URLs on a given website, while also collecting unique response headers. It supports various types of pages and handles JavaScript, CSS, and other resources gracefully.

## Features

- **Crawl URLs**: Discover all HTML URLs on a website.
- **Extract Response Headers**: Collect unique response headers while ignoring specified headers.
- **Handle Dynamic Content**: Wait for dynamic content to load and scroll to the bottom of pages.
- **Concurrency**: Use multiple workers to speed up the crawling process.
- **Configurable Options**: Limit the number of pages to crawl and specify an output file.

## Requirements

To run the script, you need to install the dependencies listed in `requirements.txt`.

1. Ensure you have Python 3.7+ installed.
2. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Command Line Arguments

- `<start_url>`: The starting URL to begin crawling.
- `--silent`: Suppresses all debug information.
- `--max-requests <number>`: Limits the number of pages to crawl.
- `--output-file <file_path>`: Writes the results to a specified file instead of printing to stdout.

### Options

- **`--silent`**: If this flag is included, debug messages will not be printed.
- **`--max-requests <number>`**: Limits the number of pages that will be crawled. This is useful for controlling the crawl depth and speed.
- **`--output-file <file_path>`**: Specifies a file path where the JSON results will be saved.

## Output

The script outputs a JSON object with two main keys:

- `urls`: A list of discovered URLs.
- `headers`: A dictionary of unique response headers with a single value per header.

### Example Output

```json
{
    "urls": [
        "https://example.com/page1",
        "https://example.com/page2"
    ],
    "headers": {
        "Content-Type": "text/html",
        "X-Frame-Options": "DENY"
    }
}
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Troubleshooting

If the script hangs or does not behave as expected:

- Ensure you are not exceeding the maximum requests limit.
- Check for any network issues or website restrictions.
- Ensure all dependencies are correctly installed.

Feel free to open an issue or contribute to the project on GitHub.

## Contributing

Contributions are welcome! Please fork the repository, make your changes, and submit a pull request.

---

Happy crawling!

