import re
from typing import Any, Dict, List, cast

import requests
from bs4 import BeautifulSoup, Tag


class ScrapeError(Exception):
    """Custom exception for HTML parsing errors."""


BASE_URL = "https://publictax.smith-county.com/Search/Results"


def make_query(query, page=1):
    """Builds and executes the search query for a given page."""
    params = {
        'Query.SearchField': '5',
        'Query.SearchText': f'{query}%',
        'Query.SearchAction': '',
        'Query.IncludeInactiveAccounts': 'False',
        'Query.PayStatus': 'Unpaid',
        'Query.PageNumber': f'{page}',
    }
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    print(f"Successfully fetched page {page} for query '{query}%'")
    return response.text


def get_results_and_pages(soup: BeautifulSoup):
    """Finds the total number of results and pages from the soup."""
    page_info_span = soup.find('span', class_='page-number')
    if not page_info_span:
        return 0, 0

    # Find total pages
    page_info_text = page_info_span.parent.get_text()
    match = re.search(r'of (\d+)', page_info_text)
    total_pages = int(match.group(1)) if match else 0

    # Find total results
    results_div = page_info_span.find_parent('div', class_='row')
    total_results = 0
    if results_div:
        results_strong_tag = results_div.find('strong')
        if results_strong_tag:
            total_results = int(results_strong_tag.get_text(
                strip=True).replace(',', ''))

    return total_results, total_pages


def get_page_details(soup: BeautifulSoup, query: str, page: int) -> List[Dict[str, Any]]:
    """Extracts account details from a page's soup using CSS selectors."""
    results = []
    for div in soup.select('div.account-card-container'):
        block: Dict[str, Any] = {"Query": f'{query}%', "Page": page}

        detail_rows = div.select("div.card-body > div.row > div.col > div.row")

        # Skip if it's not a valid real estate record
        type_tag = detail_rows[1].find(
            "span") if len(detail_rows) > 1 else None
        if not type_tag or type_tag.get_text(strip=True) != "Real":
            continue

        if len(detail_rows) > 2:
            # Acct & Due
            acct_tag = detail_rows[0].find("strong")
            due_tag = detail_rows[0].find("h4")
            block["Acct"] = acct_tag.get_text(
                strip=True) if acct_tag else "N/A"
            block["Due"] = due_tag.get_text(strip=True) if due_tag else "N/A"

            # Owner
            owner_tag = detail_rows[1].find("strong")
            block["Owner"] = owner_tag.get_text(
                strip=True) if owner_tag else "N/A"
            block["Type"] = "Real"

            # Address
            address_div = detail_rows[2].find('div')
            block["Location"] = address_div.contents[2].get_text(
                strip=True) if address_div and len(address_div.contents) > 2 else "N/A"

            block[
                "Link"] = f"https://publictax.smith-county.com/Accounts/AccountDetails?taxAccountNumber={block.get('Acct')}"
            results.append(block)

    return results


def run_full_scrape(page_limit=None) -> List[Dict[str, Any]]:
    """
    Runs the entire scraping process through all queries and pages.
    """
    # --- MODIFIED FOR BETA ---
    # Only run the query for "0" for the client's test.
    queries = ["0"]

    all_accounts = []

    try:
        for query in queries:
            all_accounts = run_scrape(query, all_accounts, page_limit)

        print(
            f"\n--- Scraping Complete. Total accounts found: {len(all_accounts)} ---")
        return all_accounts

    except requests.exceptions.RequestException as e:
        print(f"A network error occurred: {e}")
        return []
    except ScrapeError as e:
        print(f"A parsing error occurred: {e}")
        return []


def run_scrape(query, acct_list: List[Dict[str, Any]] = [], page_limit: int | None = None) -> List[Dict[str, Any]]:
    """
    Runs the scraping process for one specific query.
    """

    try:
        print(f"--- Starting Query: {query}% ---")
        # Get first page and total page count
        html_content = make_query(query, 1)
        soup = BeautifulSoup(html_content, 'html.parser')

        total_results, total_pages = get_results_and_pages(soup)

        if total_results == 0:
            print(f"No results found for query '{query}%'. Skipping.")
            return []

        print(
            f"Found {total_results} results across {total_pages} pages for query '{query}%'.")

        # Scrape first page
        page_details = get_page_details(soup, query, 1)
        acct_list.extend(page_details)
        if page_limit:
            total_pages = min(total_pages, page_limit)

        # Scrape remaining pages
        for page_num in range(2, total_pages + 1):
            html_content = make_query(query, page_num)
            soup = BeautifulSoup(html_content, 'html.parser')
            page_details = get_page_details(soup, query, page_num)
            acct_list.extend(page_details)

        print(
            f"\n--- Scraping Complete. Total accounts found: {len(acct_list)} ---")
        return acct_list

    except requests.exceptions.RequestException as e:
        print(f"A network error occurred: {e}")
        return []
    except ScrapeError as e:
        print(f"A parsing error occurred: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []
