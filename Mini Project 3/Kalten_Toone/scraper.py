import pip
import requests  # For fetching the webpage
from bs4 import BeautifulSoup  # For parsing the webpage
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import re

# URL of the webpage to scrape
url = 'https://starbucksmenuprices.com/'

# Send a request to the server
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Successfully fetched the webpage!")
else:
    print(f"Failed to fetch webpage. Status code: {response.status_code}")

# Parse the webpage content with BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

# Find all <ul> elements containing the country links
sections = soup.find_all('ul')  # Locate all <ul> elements

# Lists in Python: The result is a list, which can store multiple items.
print(sections[1])

# Extract links from the <ul> sections
country_links = []  # Empty list to store results

for section in sections:
    links = section.find_all('a')  # Find all <a> tags in each section
    for link in links:
        country_name = link.text.strip()  # Get the visible text of the link
        country_url = link.get('href')  # Get the href attribute (URL)
        country_links.append({'Country': country_name, 'URL': country_url})

df = pd.DataFrame(country_links)

# Display the first few rows of the DataFrame
print(df.head())

folder_path = './'  # Adjust to the directory where the files are stored
worldwide_latte_prices = []
# Save the DataFrame to a CSV file
df.to_csv('project3\starbucks_country_links.csv', index=False)
print("Saved country links to starbucks_country_links.csv")

# Step 4: Loop through files in the folder
for file_name in os.listdir(folder_path):
    # Check if the file matches the pattern "starbucks_prices_[country].csv"
    if file_name.startswith('starbucks_prices_') and file_name.endswith('.csv'):
        # Extract the country name from the file name
        country_name = file_name.replace('starbucks_prices_', '').replace('.csv', '').capitalize()
        
        # Load the CSV file into a DataFrame
        file_path = os.path.join(folder_path, file_name)
        df = pd.read_csv(file_path)
        
        # Step 5: Search for a row containing 'Latte'
        for _, row in df.iterrows():
            if 'latte' or 'late' in row['Item'].lower():  # Case-insensitive search for "latte"
                latte_price = row['Price']
                # Append the country name and latte price to the list
                worldwide_latte_prices.append({'Country': country_name, 'Latte Price': latte_price})
                break  # Stop after finding the first matching "latte"

# Load country data from the CSV file
csv_file = 'project3/worldwide_latte_prices.csv'  # Replace with your CSV file name
countries = pd.read_csv(csv_file)

# Set up Selenium WebDriver
driver = webdriver.Chrome()  # Ensure ChromeDriver is properly set up

# Define a function to fetch exchange rate using DuckDuckGo
def get_exchange_rate_from_duckduckgo(country_name):
    try:
        # Open DuckDuckGo and search for the exchange rate
        driver.get("https://duckduckgo.com/")
        search_box = driver.find_element(By.NAME, "q")  # Locate search bar
        search_box.clear()  # Clear any existing text
        search_box.send_keys(f"{country_name} currency to USD")  # Enter the search query
        search_box.send_keys(Keys.RETURN)  # Press Enter to search

        # Wait for results to load
        time.sleep(3)

        # Locate the input field containing the exchange rate
        rate_element = driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Currency value in USD"]')  # Adjusted selector
        exchange_rate = rate_element.get_attribute("value")  # Extract the value from the input field
        return exchange_rate
    except Exception as e:
        print(f"Failed to get exchange rate for {country_name}: {e}")
        return None
    
# Loop through each country and fetch exchange rates
exchange_rates = []
for _, row in countries.iterrows():
    country_name = row['Country']
    print(f"Fetching exchange rate for {country_name}...")
    rate = get_exchange_rate_from_duckduckgo(country_name)
    exchange_rates.append({'Country': country_name, 'Exchange Rate': rate})

# Step 4: Save the results to a new CSV file
df_exchange_rates = pd.DataFrame(exchange_rates)
output_file = 'project3/exchange_rates_duckduckgo.csv'
df_exchange_rates.to_csv(output_file, index=False)
print(f"Saved exchange rates to {output_file}")

# Close the Selenium WebDriver
driver.quit()

# Define paths
folder_path = 'project3/prices/'  # Directory containing Starbucks price files
exchange_rate_file = 'project3/exchange_rates_duckduckgo.csv'  # Pre-fetched exchange rates
output_file = 'project3/latte_index.csv'
USA_LATTE_PRICE = 4.68  # Example price of a Starbucks Latte in the USA

# Load exchange rate data
exchange_rates_df = pd.read_csv(exchange_rate_file)
exchange_rates = dict(zip(exchange_rates_df['Country'], exchange_rates_df['Exchange Rate']))

# List to store final data
latte_data = []

# Function to clean and convert price to float
def clean_price(price_str):
    price_str = re.sub(r"[^\d.]", "", price_str)  # Remove non-numeric characters except '.'
    try:
        return float(price_str)
    except ValueError:
        return None  # Return None if conversion fails

# Process each country's Starbucks price file
for file_name in os.listdir(folder_path):
    if file_name.startswith('starbucks_prices_') and file_name.endswith('.csv'):
        country_name = file_name.replace('starbucks_prices_', '').replace('.csv', '').capitalize()
        
        # Load the CSV file into a DataFrame
        file_path = os.path.join(folder_path, file_name)
        df = pd.read_csv(file_path)

        # Find latte price
        latte_price = None
        for _, row in df.iterrows():
            if 'latte' in row['Item'].lower():
                latte_price = clean_price(row['Price'])
                if latte_price is not None:
                    break
        
        if latte_price is None:
            print(f"No valid latte price found for {country_name}. Skipping...")
            continue

        # Get exchange rate from pre-fetched data
        exchange_rate = exchange_rates.get(country_name)
        if exchange_rate is None:
            print(f"Missing exchange rate for {country_name}. Skipping...")
            continue

        # Calculate PPP exchange rate
        ppp_exchange_rate = latte_price / USA_LATTE_PRICE

        expected_latte_price = 1/exchange_rate *USA_LATTE_PRICE

        overprice = (latte_price/expected_latte_price)

        # Store results
        latte_data.append({
            "Country": country_name,
            "Latte Price (Local)": latte_price,
            "Exchange Rate": exchange_rate,
            "PPP Exchange Rate": ppp_exchange_rate,
            "Expected Latte Price": expected_latte_price,
            "Over Price percent": overprice,
        })

# Save the final data to CSV
df_final = pd.DataFrame(latte_data)
df_final.to_csv(output_file, index=False)

print(f"Latte index data saved to {output_file}")

#There were eight countries for which I was able to retrieve all of this information for and include in this report. 
#I calculated the expected price of a latte based off exchange rate and used that to find the "overprice percent" of a latte.
#5/8 countries come in as underpriced for their lattes. 3/8 have overpriced lattes. 
#Most interestingly is that almost all countries have a PPP ratio >1. Meaning that their purchasing power with their currency is significantly lower than the US dollar. The one country for which I have data 
#which has a strong comparison is Italy. However, I think this has more to do with market competition in italy and less with the currency. Coffee culture in Italy is very strong. 
#This could be verified by looking at other EU countries but the data for them was not able to be collected.

#The PPP index is powerful because it gives a good glimpse at quality of life between countries.