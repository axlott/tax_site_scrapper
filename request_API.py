import json
import re
from io import BytesIO
from typing import Any, Dict, List, cast

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag


class ScrapeError(Exception):
    """Custom exception for HTML parsing errors."""


BASE_URL = "https://publictax.smith-county.com/Search/Results"


def make_query(query, page=1):
    params = {
        # This likely represents the field to search (e.g., Owner Name)
        'Query.SearchField': '5',
        # The name or text you want to find
        f'Query.SearchText': f'{query}%',
        'Query.SearchAction': '',
        'Query.IncludeInactiveAccounts': 'False',
        # You could change this to 'Paid' or leave it empty
        'Query.PayStatus': 'Unpaid',
        # You could change this to 'Paid' or leave it empty
        'Query.PageNumber': f'{page}',
    }
    response = requests.get(BASE_URL, params=params)

    # Raise an exception if the request returned an error code
    response.raise_for_status()

    # The server's response will likely be HTML or JSON.
    # If it's the data you see on the page, you've succeeded!
    print("\nSuccess! The server responded.")

    # If the response is JSON, you can view it like this:
    # print(response.json())

    # If the response is HTML, you can view it like this:
    return response.text


def get_results(soup):
    for div in soup.find_all('div'):
        # .get_text() joins all text from child elements

        if 'results found for' in div.get_text() and len(div) == 5:
            if div.find('div') is not None:
                continue

            return int(div.find('strong').get_text())
    else:
        return None


def get_pages(soup):
    # 3. Find the total number of pages
    # Find the span with class 'page-number' and get its parent div's text
    page_info_span = soup.find('span', class_='page-number')
    # This will be "(showing page 1 of 39)"
    if page_info_span is None:
        return None
    page_info_div = page_info_span.parent
    # This will be "(showing page 1 of 39)"
    if page_info_div is None:
        return None
    page_info_text = page_info_div.get_text()

    # Use a regular expression to find the number after "of "
    match = re.search(r'of (\d+)', page_info_text)
    return int(match.group(1)) if match else 0


def get_first_page_results(query):
    page = 1
    html_query = make_query(query, page)

    # 1. Parse the HTML content with Beautiful Soup
    soup = BeautifulSoup(html_query, 'html.parser')

    # --- PARSING CODE ENDS HERE ---

    # 2. Find the total number of results from the <strong> tag and the total number of pages
    total_results = get_results(soup)

    if total_results is None:
        raise ScrapeError(
            f"Could not find total results for query: {query}")

    total_pages = get_pages(soup)

    if total_pages is None:
        raise ScrapeError(
            f"Could not find total pages for query: {query}")

    print("\n✅ Search successful!")
    print(f"Total Results Found: {total_results}")
    print(f"Total Pages: {total_pages}")
    return (total_results, total_pages, soup)

# div.select("div.card-body > div.row > div.col > div.row")


def get_page_details(soup: BeautifulSoup, query, page) -> List[Dict[str, Any]]:
    """
    Extracts account details from a page's soup using CSS selectors.
    """
    results = []
    # Use select() to robustly find the main containers by class
    for div in soup.select('div.account-card-container'):
        block: Dict[str, Any] = {"Query": f'{query}%', "Page": page}

        # The selector finds only the direct .row children of .card-body
        # This replaces three nested .find() calls and a .find_all()
        detail_rows = div.select("div.card-body > div.row > div.col > div.row")

        for i, detail in enumerate(detail_rows):
            if i == 0:  # Account Number and Total Due
                acct_tag = detail.find("strong")
                due_tag = detail.find("h4")
                if acct_tag:
                    block["Acct"] = acct_tag.get_text(strip=True)
                else:
                    raise ScrapeError(
                        f"Could not find the account number in result block: {block}")
                if due_tag:
                    block["Due"] = due_tag.get_text(strip=True)
                else:
                    raise ScrapeError(
                        f"Could not find the total due in result block: {block}")

            elif i == 1:  # Owner Name and Type
                owner_tag = detail.find("strong")
                type_tag = detail.find("span")
                if owner_tag:
                    block["Owner"] = owner_tag.get_text(strip=True)
                if type_tag:
                    block["Type"] = type_tag.get_text(strip=True)
                    # TODO: Comment this if you want to filter out non-real estate types
                    if block["Type"] != "Real":
                        break  # Skip non-real estate types

            elif i == 2:  # Address
                # Using .find() is still great for simple cases
                address_div = cast(Tag, detail.find('div'))
                if address_div and len(address_div.contents) > 2:
                    block["Location"] = address_div.contents[2].get_text(
                        strip=True)
                else:
                    raise ScrapeError(
                        f"Could not find the address in result block: {block.get('Acct')}")
        else:
            # Find the details link using a CSS selector
            block[
                "Link"] = f"https://publictax.smith-county.com/Accounts/AccountDetails?taxAccountNumber={block.get('Acct')}"

            if len(block) == 8:
                results.append(block)
            else:
                raise ScrapeError(
                    f"Could not find all required fields in result block: {block}")

    return results


def run_full_scrape() -> List[Dict[str, Any]]:

    # The base URL from the website
    # (e.g., "https://publictax.smith-county.com")

    # Define your search parameters. You can change these!
    # Let's try searching for a property owner named "Jones"
    page = 1
    queries = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", "G",
               "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    queries = ["0"]

    try:
        account_dets = []
        for query in queries:
            results, pages, soup = get_first_page_results(query)
            if results is None or pages is None:
                raise ScrapeError(
                    "Could not find results or pages in the HTML.")
            temp = get_page_details(soup, query, page)
            if temp:
                account_dets.extend(temp)
                print(results)
            else:
                print(
                    f"\nNo results found on page 1 for query: {query}%")
            pages = 2  # TODO: Remove this line to scrape all pages
            for page in range(2, pages + 1):
                html_query = make_query(query, page)
                soup = BeautifulSoup(html_query, 'html.parser')
                temp = get_page_details(soup, query, page)
                if temp:
                    account_dets.extend(temp)
                    print(f"\nPage {page} Results:")
                else:
                    print(
                        f"\nNo results found on page {page} for query: {query}%")
                    continue

        return account_dets

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred: {e}")
        return []
    except (AttributeError, ValueError) as e:
        print(
            f"\nCould not parse the HTML. The page structure might have changed.\n\n{e}")
        return []
        # print(response.text) # Uncomment this to see the raw HTML if parsing fails
    except ScrapeError as e:
        print(f"\nHTML parsing error during scrapping: {e}")
        return []


if __name__ == "__main__":
    # Run the full scrape function
    results = run_full_scrape()
    print(f"\nTotal Results: {len(results)}")

    df = pd.read_json(json.dumps(results, indent=4, ensure_ascii=False))
    # df.to_csv('results.csv', encoding='utf-8', index=True)

    # df.to_excel('results.xlsx', index=True)
    temp_xlsx = BytesIO()
    df.to_excel(temp_xlsx, index=True)

    with open('results.xlsx', 'wb+') as f:
        f.write(temp_xlsx.getvalue())

    print("Results saved to results.csv")
    print("Scraping completed successfully.")
