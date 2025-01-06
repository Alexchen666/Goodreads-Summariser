# GoodReads Review Summariser

Summarise book reviews with the power of LLM.

Want to know more about a book before reading it?

LLM can help you! Use LLM to summarise the reviews.

## Installation

1. Create a Python environment as specified in `pyproject.toml`.
2. Download [Ollama](https://ollama.com/) and pull the [llama3.2:3b](https://ollama.com/library/llama3.2) model.
3. Download the repo and execute `demo.py` using `marimo run demo.py`.
4. Enjoy the summariser!

## How to Use?
1. Click the "SHARE" button (represented by an icon) in the upper right corner of your chosen book's Goodreads page.
2. Click the "Copy URL" button.
3. Paste the link on this page -- that's it!

## How it Works?
The programme scrapes the GoodReads webpage and extracts the review content for the [llama3.2:3b](https://ollama.com/library/llama3.2) model to generate the summary.

GoodReads Scraping Reference: https://rakaarfi.medium.com/scrape-goodreads-book-reviews-using-python-a53252284726
