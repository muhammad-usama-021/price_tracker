import requests
from bs4 import BeautifulSoup
import sqlite3
import os
from notifier import send_email
from dotenv import load_dotenv
import time
import random

# Load environment variables
load_dotenv()

# User-Agent to mimic a browser visit
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

DATABASE = 'database.db'

def get_product_price(url, retries=3):
    """
    Scrape the product page to extract the current price.
    Retries scraping a few times if it fails to find the price.
    """
    try:
        for attempt in range(retries):
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()  # Raise HTTPError for bad responses
            
            # Wait for 10 seconds after the link is opened
            time.sleep(3)  # Delay of 3 seconds
            
            soup = BeautifulSoup(response.content, 'html.parser')

            # Check if the 'a-box-group' div is present
            box_group = soup.find('div', class_='a-box-group')
            if box_group:
                print("'a-box-group' found, now searching for price...")

                # Try multiple ways to find the price on the page
                price = box_group.find('span', class_='a-offscreen')  # Common class for prices on Amazon

                # Try additional selectors if the first one fails
                if not price:
                    price = box_group.find(id='priceblock_ourprice') or box_group.find(id='priceblock_dealprice')

                if price:
                    price_text = price.get_text().strip().replace('₹', '').replace(',', '').strip()
                    current_price = float(price_text)
                    print(f"Attempt {attempt + 1}: Fetched price: ₹{current_price}")
                    return current_price
                else:
                    print(f"Attempt {attempt + 1}: Price not found in 'a-box-group', retrying...")
            else:
                print(f"Attempt {attempt + 1}: 'a-box-group' not found, retrying...")
            
            time.sleep(random.uniform(1, 3))  # Random sleep before retry

        # If no price is found after retries
        print(f"Price not found for URL: {url} after {retries} attempts.")
        return None

    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None
    except ValueError:
        print(f"Error parsing price for URL: {url}")
        return None
def fetch_tracked_products():
    """
    Retrieve all products from the database that are being tracked.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

def update_price_history(product_id, price):
    """
    Insert the current price into the price_history table.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO price_history (product_id, price) VALUES (?, ?)",
        (product_id, price)
    )
    conn.commit()
    conn.close()

def check_and_notify(product, current_price):
    """
    Check if the current price is below or equal to the target price.
    If so, send a notification.
    """
    product_id, name, url, target_price = product  # product is a tuple
    if current_price <= target_price:
        subject = f"Price Alert: {name} is now ₹{current_price}"
        body = f"The price of '{name}' has dropped to ₹{current_price}.\nCheck it out here: {url}"
        recipient_email = os.getenv('RECIPIENT_EMAIL')  # Define in .env
        send_email(subject, body, recipient_email)

def scrape_prices():
    """
    Main function to scrape prices for all tracked products.
    """
    products = fetch_tracked_products()
    if not products:
        print("No products to track.")
        return

    for product in products:
        product_id, name, url, target_price = product  # product is a tuple
        print(f"Checking price for '{name}'...")
        current_price = get_product_price(url)
        
        if current_price:
            update_price_history(product_id, current_price)
            print(f"Current price for '{name}': ₹{current_price}")  # Adjust the currency if needed
            
            if current_price <= target_price:  # Compare with the unpacked target_price
                print(f"Price alert for '{name}'!")
                check_and_notify(product, current_price)
        else:
            print(f"Failed to retrieve price for '{name}'.")

def main():
    scrape_prices()

if __name__ == "__main__":
    main()
