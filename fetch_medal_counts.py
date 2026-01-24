#!/usr/bin/env python3
"""
BBO 2026 Medal Category Counts Fetcher

This script fetches the Current Medal Category Counts table from the
BBO website and converts it to a CSV file.

Usage:
    python3 fetch_medal_counts.py

Output:
    - medal_category_counts.csv: Extracted table data
"""

import csv
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def fetch_medal_counts(url: str) -> list:
    """
    Fetch the HTML page and extract the table under 'Current Medal Category Counts' H2.
    
    Args:
        url: The URL to fetch
        
    Returns:
        list: List of rows, where each row is a list of cell values
    """
    print(f"Fetching data from {url}...")
    
    # Fetch the HTML page
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the H2 element containing 'Current Medal Category Counts'
    h2_element = soup.find('h2', string=lambda text: text and 'Current Medal Category Counts' in text)
    
    if not h2_element:
        raise ValueError("Could not find H2 element with 'Current Medal Category Counts'")
    
    print(f"Found H2 element: {h2_element.text}")
    
    # Find the table that follows the H2 element
    # Try to find a table that is a sibling or child of the H2's parent
    table = h2_element.find_next('table')
    
    if not table:
        raise ValueError("Could not find table after 'Current Medal Category Counts' heading")
    
    print("Found table, extracting data...")
    
    # Extract table data
    rows = []
    
    # Get header row if present
    thead = table.find('thead')
    if thead:
        header_row = thead.find('tr')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            rows.append(headers)
    
    # Get body rows
    tbody = table.find('tbody') or table
    for tr in tbody.find_all('tr'):
        cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
        if cells:  # Only add non-empty rows
            # Clean the cells: remove '[Full]' or '[full]' from values
            cleaned_cells = [cell.replace('[Full]', '').replace('[full]', '').strip() for cell in cells]
            rows.append(cleaned_cells)
    
    print(f"Extracted {len(rows)} rows")
    return rows


def save_to_csv(data: list, output_file: str):
    """
    Save the extracted data to a CSV file.
    
    Args:
        data: List of rows to save
        output_file: Path to the output CSV file
    """
    print(f"Saving data to {output_file}...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    
    print(f"Successfully saved {len(data)} rows to {output_file}")


def main():
    """Main function to fetch and convert the medal counts table."""
    url = 'https://bcoemfix.bluebonnetbrewoff.org/index.php?section=entry'
    output_file = 'medal_category_counts.csv'
    
    if not HAS_REQUESTS:
        print("Error: 'requests' and 'beautifulsoup4' modules are required.")
        print("\nTo install them, run:")
        print("  pip install requests beautifulsoup4")
        print("\nAlternatively, if you already have medal_category_counts.csv,")
        print("you can use it as-is (no update needed).")
        print("\nNote: This script is only needed if you want to fetch the latest")
        print("data from the BBO website. Your existing CSV file is likely current.")
        return
    
    try:
        # Fetch the data
        data = fetch_medal_counts(url)
        
        if not data:
            print("No data extracted from the table")
            return
        
        # Save to CSV
        save_to_csv(data, output_file)
        
        # Display a preview
        print("\nPreview of extracted data:")
        for i, row in enumerate(data[:5]):  # Show first 5 rows
            print(f"Row {i}: {row}")
        
        if len(data) > 5:
            print(f"... and {len(data) - 5} more rows")
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    main()
