import os
import pandas as pd
import re  # To clean currency values

# Define paths
folder_path = 'project3/prices/'  # Directory containing Starbucks price files
exchange_rate_file = 'project3/exchange_rates_duckduckgo.csv'  # Pre-fetched exchange rates
output_file = 'project3/latte_index.csv'
USA_LATTE_PRICE = 5.50  # Example price of a Starbucks Latte in the USA

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

        # Store results
        latte_data.append({
            "Country": country_name,
            "Latte Price (Local)": latte_price,
            "Exchange Rate": exchange_rate,
            "PPP Exchange Rate": ppp_exchange_rate,
        })

# Save the final data to CSV
df_final = pd.DataFrame(latte_data)
df_final.to_csv(output_file, index=False)

print(f"Latte index data saved to {output_file}")
