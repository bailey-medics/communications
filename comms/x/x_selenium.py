from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import time

# Load environment variables from .env file
load_dotenv(override=True)


def post_tweet(message):
    # Set up the WebDriver
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    try:
        # Open Twitter login page
        driver.get("https://twitter.com/login")
        time.sleep(100)  # Wait for the page to load

        # Find and fill the username field
        username_field = driver.find_element(By.NAME, "session[username_or_email]")
        username_field.send_keys(os.getenv("TWITTER_USERNAME"))

        # Find and fill the password field
        password_field = driver.find_element(By.NAME, "session[password]")
        password_field.send_keys(os.getenv("TWITTER_PASSWORD"))
        password_field.send_keys(Keys.RETURN)
        time.sleep(3)  # Wait for the login to complete

        # Find and click the tweet button
        tweet_button = driver.find_element(By.XPATH, '//a[@href="/compose/tweet"]')
        tweet_button.click()
        time.sleep(3)  # Wait for the tweet modal to open

        # Find and fill the tweet text area
        tweet_textarea = driver.find_element(
            By.XPATH, '//div[@aria-label="Tweet text"]'
        )
        tweet_textarea.send_keys(message)

        # Find and click the tweet submit button
        tweet_submit_button = driver.find_element(
            By.XPATH, '//div[@data-testid="tweetButtonInline"]'
        )
        tweet_submit_button.click()
        time.sleep(3)  # Wait for the tweet to be posted

        print("Tweet posted successfully!")

    except Exception as e:
        print(f"Failed to post tweet. Error: {e}")

    finally:
        # Close the WebDriver
        driver.quit()


# Example usage
if __name__ == "__main__":
    post_tweet("Hello, world! This is a test tweet from letsdodigital.org.")
