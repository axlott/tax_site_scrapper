document.getElementById('scrapeButton').addEventListener('click', async () => {
    const button = document.getElementById('scrapeButton');
    const statusText = document.getElementById('statusText');
    const spinner = document.getElementById('spinner');

    // Disable button and show loading state
    button.disabled = true;
    spinner.style.display = 'block';
    statusText.textContent = 'Scraping in progress... This may take several minutes. Please do not close this window.';

    try {
        const response = await fetch('/run-scraper', {
            method: 'POST',
        });

        if (response.ok) {
            // The browser will handle the download automatically.
            // We need to get the blob to know when the download is ready.
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            // Get filename from response headers if possible, otherwise use a default
            const disposition = response.headers.get('Content-Disposition');
            let filename = 'scraped_tax_data.xlsx';
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }
            a.setAttribute('download', filename);
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            statusText.textContent = 'Download complete! Ready for another scrape.';
        } else {
            // Handle HTTP errors
            const errorText = await response.text();
            statusText.textContent = `Error: ${errorText}`;
        }
    } catch (error) {
        // Handle network errors
        console.error('Fetch error:', error);
        statusText.textContent = 'An error occurred. Could not connect to the server.';
    } finally {
        // Re-enable button and hide spinner
        button.disabled = false;
        spinner.style.display = 'none';
    }
});
