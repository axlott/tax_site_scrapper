# Save this as app.py
import json
from io import BytesIO

import pandas as pd
from flask import Flask, Response, request

from request_API import \
    run_full_scrape  # Assume your main logic is in a function

app = Flask(__name__)

# This is the secret endpoint your client's webpage will call


@app.route('/run-scraper', methods=['POST'])
def run_scraper_endpoint():
    # You could add a secret key here for extra security
    # secret_key = request.json.get('key')
    # if secret_key != 'my-secret-beta-key':
    #     return "Unauthorized", 401

    print("Scraper job started...")

    # Run your main scraping function which returns the data
    # For simplicity, let's assume it returns a list of dicts
    list_of_results = run_full_scrape()

    # Convert the list of dictionaries to a CSV string
    if not list_of_results:
        return "No results found.", 404

    csv_string = BytesIO()
    df = pd.read_json(json.dumps(
        list_of_results, indent=4, ensure_ascii=False))
    df.to_excel(csv_string, index=True)

    # Send the CSV back as a file download
    return Response(
        csv_string.getvalue(),
        # mimetype="text/csv",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition":
                 "attachment; filename=beta-results.xlsx"},
        status=200)


if __name__ == '__main__':
    # You would run this on a simple server (like PythonAnywhere, Heroku, etc.)
    app.run(debug=True)
