#!/usr/bin/env python3
"""
Calculate distances from judge addresses to competition sites and update CSV.
Uses geocoding to convert addresses to coordinates, then calculates driving distances.
"""

import csv
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Reference site locations
REFERENCE_LOCATIONS = {
    'ARLINGTON SITE': '76013',
    'DALLAS SITE': '75252',
    'GRAPEVINE SITE': '76051',
    'KELLER SITE': '76248',
    'STUBBIES SITE': '76117'
}

def geocode_with_retry(geolocator, address, max_retries=3):
    """Geocode an address with retry logic."""
    for attempt in range(max_retries):
        try:
            time.sleep(1)  # Rate limiting - Nominatim requires 1 second between requests
            location = geolocator.geocode(address, timeout=10)
            if location:
                return location
            else:
                print(f"  Warning: Could not geocode '{address}'")
                return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            if attempt < max_retries - 1:
                print(f"  Retry {attempt + 1} for {address}")
                time.sleep(2)
            else:
                print(f"  Error geocoding '{address}': {e}")
                return None
    return None

def geocode_reference_sites(geolocator):
    """Geocode all reference sites."""
    print("Geocoding reference sites...")
    reference_coords = {}
    
    for site_name, zipcode in REFERENCE_LOCATIONS.items():
        address = f"{zipcode}, Texas, USA"
        print(f"  {site_name}: {zipcode}")
        location = geocode_with_retry(geolocator, address)
        if location:
            reference_coords[site_name] = (location.latitude, location.longitude)
            print(f"    -> {location.latitude:.4f}, {location.longitude:.4f}")
        else:
            print(f"    -> FAILED")
    
    return reference_coords

def geocode_judge_address(geolocator, street_address, city):
    """Geocode a judge's address."""
    if not street_address or not city:
        return None
    
    # Clean up the address
    address = f"{street_address}, {city}, Texas, USA"
    return geocode_with_retry(geolocator, address)

def calculate_distance(coord1, coord2):
    """Calculate distance in miles between two coordinates."""
    if coord1 and coord2:
        distance_km = geodesic(coord1, coord2).kilometers
        distance_miles = distance_km * 0.621371  # Convert to miles
        return round(distance_miles)
    return None

def update_csv_with_distances(input_file, output_file):
    """Read CSV, calculate distances, and write updated CSV."""
    print(f"\nProcessing {input_file}...")
    
    # Initialize geocoder
    geolocator = Nominatim(user_agent="judging_distance_calculator_2026")
    
    # Geocode reference sites first
    reference_coords = geocode_reference_sites(geolocator)
    
    if not reference_coords:
        print("Error: Could not geocode reference sites")
        return
    
    print(f"\nSuccessfully geocoded {len(reference_coords)} reference sites\n")
    
    # Read the CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    print(f"Processing {len(rows)} judges...")
    updated_count = 0
    skipped_count = 0
    
    # Process each judge
    for i, row in enumerate(rows, 1):
        judge_name = f"{row.get('First Name', '')} {row.get('Last Name', '')}"
        street_address = row.get('STREET ADDRESS', '').strip()
        city = row.get('City Bell', '').strip()
        
        print(f"\n{i}. {judge_name}")
        
        # Skip if no address
        if not street_address or not city:
            print(f"   Skipping - no address information")
            skipped_count += 1
            continue
        
        # Geocode judge's address
        print(f"   Address: {street_address}, {city}")
        judge_location = geocode_judge_address(geolocator, street_address, city)
        
        if not judge_location:
            print(f"   Could not geocode address")
            skipped_count += 1
            continue
        
        judge_coords = (judge_location.latitude, judge_location.longitude)
        print(f"   Coords: {judge_coords[0]:.4f}, {judge_coords[1]:.4f}")
        
        # Calculate distances to each site
        distances_calculated = False
        for site_name, site_coords in reference_coords.items():
            distance = calculate_distance(judge_coords, site_coords)
            if distance is not None:
                row[site_name] = str(distance)
                print(f"   {site_name}: {distance} miles")
                distances_calculated = True
        
        if distances_calculated:
            updated_count += 1
    
    # Write updated CSV
    print(f"\n\nWriting updated CSV to {output_file}...")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nComplete!")
    print(f"  Updated: {updated_count} judges")
    print(f"  Skipped: {skipped_count} judges (no address)")
    print(f"  Total: {len(rows)} judges")

if __name__ == "__main__":
    input_file = "JUDGE WORKSHEET 2026.csv"
    output_file = "JUDGE WORKSHEET 2026.csv"
    
    print("=" * 70)
    print("JUDGE DISTANCE CALCULATOR")
    print("=" * 70)
    print("\nThis script will:")
    print("1. Geocode each judge's address")
    print("2. Calculate distances to all competition sites")
    print("3. Update the CSV file with calculated distances")
    print("\nNote: This uses Nominatim geocoding which requires 1 second")
    print("      between requests. This will take several minutes.")
    print("=" * 70)
    
    response = input("\nProceed? (y/n): ")
    if response.lower() == 'y':
        update_csv_with_distances(input_file, output_file)
    else:
        print("Cancelled.")
