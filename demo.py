import marimo

__generated_with = "0.10.9"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # GoodReads Review Summariser

        GoodReads Scraping Reference: https://rakaarfi.medium.com/scrape-goodreads-book-reviews-using-python-a53252284726

        ## How to Use?

        1. Click the "SHARE" button (represented by an icon) in the upper right corner of your favourite book's Goodreads page.
        2. Click the "Copy URL" button.
        3. Paste the link on this page! That's it!

        ## How it Works?

        The programme scrapes the GoodReads webpage and extracts the review contents for the [llama3.2:3b](https://ollama.com/library/llama3.2) model to generate the summary.

        ---
        """
    )
    return


@app.cell
def _(mo):
    url = mo.ui.text(label='GoodReads Link (Via Share)', placeholder='Required', kind='url', full_width=True)
    run = mo.ui.run_button(label='Summarise!', kind='success')
    return run, url


@app.cell
def _(mo, run, url):
    mo.vstack([url, mo.center(run)])
    return


@app.cell
def _(
    extract_content,
    find_review,
    llm_summarise,
    mo,
    review_cleaning,
    run,
    url,
):
    if run.value:
        mo.output.append('Step 1: Start Extracting Reviews...')
        try:
            title, author, review = find_review(url.value)
        except Exception as e:
            mo.stop(predicate=True, output=mo.md(f'There is an error in Step 1: {e}'))
        mo.output.append('Reviews Extracted!\n')
        mo.output.append('Step 2: Cleaning Reviews...')
        try:
            df = review_cleaning(review)
            content = extract_content(df)
        except Exception as e:
            mo.stop(predicate=True, output=mo.md(f'There is an error in Step 2: {e}'))
        mo.output.append('Reviews Are Clean!')
        mo.output.append('Step 3: LLM Summarising...')
        try:
            ans = llm_summarise(content)
        except Exception as e:
            mo.stop(predicate=True, output=mo.md(f'There is an error in Step 3: {e}'))
        mo.output.append('Finished!\n')
        mo.output.replace(mo.md(f"""# Summary

        The reviews from the book '{title}' by {author} have been summarised as follows:

        {ans}"""))
    return ans, author, content, df, review, title


@app.cell
def _():
    import requests
    from bs4 import BeautifulSoup as bs
    import polars as pl
    from langchain_ollama import ChatOllama
    import marimo as mo
    return ChatOllama, bs, mo, pl, requests


@app.cell
def _():
    system_prompt = """Please generate an English summary on the reviews provided by the user. It should mention the postivie aspects, critical feedback, and a balanced conclusion based on the provided information.

    Specifically, you should include the following points:

    * The pacing and flow of the story
    * Character development and memorable personalities
    * Plot structure and storytelling elements
    * Any other consistently praised features

    Please ensure your analysis reflects the frequency and intensity of specific comments rather than just listing individual opinions.
    """
    return (system_prompt,)


@app.cell
def _(bs, requests):
    def find_review(url: str) -> tuple:
        """
        This function scrapes the reviews from a Goodreads book page.
        It takes the URL of the book page as input and returns a list of dictionaries,
        where each dictionary contains the details of a single review.

        Args:
        url (str): The URL of the Goodreads book page.

        Returns:
        tuple: A tuple containing the title of the book, the author of the book, and a list of dictionaries
        """


        # Headers to mimic a real browser request and avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        }
        # Send a GET request to fetch the page content
        response = requests.get(url, headers=headers)
        # Parse the HTML content using BeautifulSoup
        soup = bs(response.content, 'html.parser')

        # Extract the book title and author name
        title = soup.find('h1', class_='Text Text__title1').get_text()
        author = soup.find('span', class_='ContributorLink__name').get_text()

        # Find all div tags containing review sections
        reviews_list = soup.find_all('div', class_='ReviewsList')

        # Select the relevant div that contains the reviews
        reviews_tag = reviews_list[1] # Only scrape the second <div>

        articles = reviews_tag.find_all('article', class_='ReviewCard')

        all_reviews = []

        # Loop through each review (article tag) and extract the necessary details
        for idx, i in enumerate(articles):
            # Extract Reviewer Profile Information
            profile_info = i.find('section', class_='ReviewerProfile__info')

            # Extract the reviewer's name and profile link
            name = profile_info.find('a').get_text()
            link_profile = profile_info.find('a').get('href')

            # Extract the number of books (if available), reviews, and followers and check if the reviewer is an author
            profile_meta = profile_info.find('div', class_='ReviewerProfile__meta')
            spans = profile_meta.find_all('span')  # Find all span tags inside profile_meta

            # Initialize default values
            check_author = False
            books_amount = None
            reviews_amount = 'Not Found'
            followers_amount = 'Not Found'

            for span in spans:
                span_text = span.get_text(strip=True)

                # Check if the span contains 'books'
                if 'books' in span_text:
                    books_amount = span_text

                # Check if the span contains 'reviews'
                elif 'reviews' in span_text:
                    reviews_amount = span_text

                # Check if the span contains 'followers'
                elif 'followers' in span_text:
                    followers_amount = span_text

                # Check if the span contains 'Author'
                elif 'Author' in span_text:
                    check_author = span_text

            # Store reviewer profile info in a dictionary
            profile = {
                'Name': name,
                'Link Profile': link_profile,
                'An Author': bool(check_author), # Will be False if not available
                'Books': books_amount,  # Will be None if not available
                'Reviews Amount': reviews_amount,  # Will be Not Found if not available
                'Followers Amount': followers_amount  # Will be Not Found if not available
            }

            # Extract the rating (stars) given by the reviewer
            shelf_status = i.find('div', class_='ShelfStatus')

            # Reviewer can give a rating (stars) or not
            try:
                rating_given = shelf_status.find('span', class_='RatingStars RatingStars__small').get('aria-label')
            except:
                rating_given = 'No Rating Given'
            # Extract the review content
            content = i.find('span', class_='Formatted').get_text(strip=True)
            # Create a dictionary with all the extracted data for this review
            data = {
                'Index': idx + 1,
                'Profile Info': profile,
                'Rating': rating_given,
                'Content': content
            }
            # Append the review data to the list of all reviews
            all_reviews.append(data)

        return (title, author, all_reviews)
    return (find_review,)


@app.cell
def _(pl):
    def review_cleaning(review: list) -> pl.DataFrame:
        """
        This function creates a Polars DataFrame from the list of dictionaries containing the review data.
        Then it cleans the review data by extracting the necessary information from the 'Profile Info' column.
        It also converts the 'Reviews Amount' and 'Followers Amount' columns to integers.

        Args:
        df (pl.DataFrame): A Polars DataFrame containing the review data.

        Returns:
        pl.DataFrame: A cleaned Polars DataFrame with the necessary information extracted.
        """
        df = pl.DataFrame(review)

        df = df.unnest('Profile Info').drop('Link Profile', 'Index', 'Books', 'An Author').with_columns(
            pl.col('Reviews Amount').str.replace('reviews', '').str.replace('review', '')\
                .str.replace(' ', '').str.replace(',', '').str.replace('NotFound', '0').cast(pl.Int32).alias('Reviews Amount'),
            pl.col('Followers Amount').str.replace(r'(\d+(?:\.\d+)?)[kK]\s+followers', 
                                                (pl.col('Followers Amount').str.extract(r'(\d+(?:\.\d+)?)', group_index=1)\
                                                    .cast(pl.Float64) * 1000).cast(pl.Int32))\
                .str.replace('followers', '').str.replace('follower', '')\
                .str.replace(' ', '').str.replace(',', '').cast(pl.Int32).alias('Followers Amount'),
            pl.col('Rating').str.extract(r'Rating (\d+) out of').cast(pl.Int32).alias('Rating')
            )

        return df
    return (review_cleaning,)


@app.cell
def _(pl):
    def extract_content(df: pl.DataFrame) -> str:
        """
        This function extracts the review content from the Polars DataFrame.

        Args:
        df (pl.DataFrame): A Polars DataFrame containing the review data.

        Returns:
        str: A string containing the review content.
        """

        content = df.select(pl.col('Content').str.join('\n')).to_dicts()
        return content[0]['Content']
    return (extract_content,)


@app.cell
def _(ChatOllama, system_prompt):
    def llm_summarise(content: str, system_prompt: str=system_prompt, model: str='llama3.2:3b') -> str:
        """
        This function generates a summary of the review content using a language model.

        Args:
        content (str): The review content to be summarised.
        system_prompt (str): The system prompt to be used for the summarisation task.
        model (str): The name of the language model to be used for summarisation.

        Returns:
        str: A string containing the summary of the review content.
        """
        llm = ChatOllama(
            model = model,
            temperature = 0.0
        )

        messages = [
            ("system", system_prompt),
            ("human", content),
        ]
        ans = llm.invoke(messages).content
        return ans
    return (llm_summarise,)


if __name__ == "__main__":
    app.run()
