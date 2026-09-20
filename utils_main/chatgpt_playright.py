""" d
run: `playwright install` on first run
"""

import os
from time import sleep

from playwright.sync_api import sync_playwright

# Define the user data directory path
USER_DATA_DIR = "./user_data"

# Ensure the directory exists
os.makedirs(USER_DATA_DIR, exist_ok=True)

with sync_playwright() as p:
    # Launch the browser with persistent context
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,  # Set to True for headless mode
    )

    # Access the context's first page
    page = browser.pages[0] if browser.pages else browser.new_page()

    # Navigate to a website
    page.goto("https://chatgpt.com")

    # Example: Print cookies
    cookies = page.context.cookies()
    print("Cookies:", cookies)

    sleep(10)

    # Close the browser but retain session data
    # browser.close()

# On the next run, cookies and session data will persist
# On the next run, cookies and session data will persist
