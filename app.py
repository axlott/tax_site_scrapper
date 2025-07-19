import json
from io import BytesIO

import pandas as pd
from flask import Flask, Response, render_template

from request_API import run_full_scrape

app = Flask(__name__)


@app.route('/')
def index():
    """Serves the frontend HTML page."""
    return render_template('index.html')


@app.route('/run-scraper', methods=['POST'])
def run_scraper_endpoint():
    """Runs the scraper and returns the results as an Excel file."""
    print("Scraper job started via API request...")

    list_of_results = run_scrape()

    if not list_of_results:
        print("Scraping returned no results.")
        return "No results found.", 404

    print(
        f"Scraping finished. Found {len(list_of_results)} records. Preparing Excel file.")

    # Use an in-memory buffer for the Excel file
    output_buffer = BytesIO()
    df = pd.DataFrame(list_of_results)

    # Use the XlsxWriter engine for better compatibility
    with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='ScrapedData')
        # Auto-adjust columns' width
        for column in df:
            column_length = max(df[column].astype(
                str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['ScrapedData'].set_column(
                col_idx, col_idx, column_length)

    # Important: seek to the beginning of the buffer before sending
    output_buffer.seek(0)

    return Response(
        output_buffer.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=scraped_tax_data.xlsx"},
        status=200
    )


@app.route('/run-full-scraper', methods=['POST'])
def run_full_scraper_endpoint():
    """Runs the scraper and returns the results as an Excel file."""
    print("Scraper job started via API request...")

    list_of_results = run_full_scrape()

    if not list_of_results:
        print("Scraping returned no results.")
        return "No results found.", 404

    print(
        f"Scraping finished. Found {len(list_of_results)} records. Preparing Excel file.")

    # Use an in-memory buffer for the Excel file
    output_buffer = BytesIO()
    df = pd.DataFrame(list_of_results)

    # Use the XlsxWriter engine for better compatibility
    with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='ScrapedData')
        # Auto-adjust columns' width
        for column in df:
            column_length = max(df[column].astype(
                str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['ScrapedData'].set_column(
                col_idx, col_idx, column_length)

    # Important: seek to the beginning of the buffer before sending
    output_buffer.seek(0)

    return Response(
        output_buffer.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=scraped_tax_data.xlsx"},
        status=200
    )


if __name__ == '__main__':
    app.run(debug=True)
