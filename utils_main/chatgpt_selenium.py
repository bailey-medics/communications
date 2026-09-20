import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def send_prompt_to_chatgpt(prompt):
    # Path to your WebDriver
    driver_path = "./utils/chromedriver"
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service)

    try:
        # Open ChatGPT
        driver.get("https://chat.openai.com/")
        time.sleep(
            10
        )  # Wait for manual login or adjust for automation if possible

        # Locate the input box (update the selector if the site changes)
        input_box = driver.find_element(By.TAG_NAME, "textarea")

        # Send the prompt
        input_box.send_keys(prompt)
        input_box.send_keys(Keys.RETURN)

        # Wait for the response to load
        time.sleep(10)  # Adjust based on response time

        # Retrieve the response (update selector as needed)
        response_elements = driver.find_elements(
            By.CLASS_NAME, "message"
        )  # Replace 'message' with the actual class
        response_text = response_elements[
            -1
        ].text  # Assuming the last message is the bot's response

        return response_text

    finally:
        driver.quit()


# Example usage
prompt = "What is the capital of France?"
response = send_prompt_to_chatgpt(prompt)
print("ChatGPT Response:", response)
print("ChatGPT Response:", response)
