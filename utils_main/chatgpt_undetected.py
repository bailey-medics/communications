import os
import pickle
import sys
import time
from pathlib import Path
from time import sleep

import undetected_chromedriver as uc
from dotenv import load_dotenv
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TEST_PROMPT = """You will be creating social comms pushes. Read the information below. From this text, create a title, LinkedIn blurb (named long_blurb) and twitter blurb (named short_blurb). Wrap each section in triple single quotation marks, as below

'''title:A title'''
'''long_blurb:A long blurb'''
'''short_blurb:A short blurb'''

Information:

Digital healthcare
"""


class ChatGPT:
    chatgpt_url: str = "https://chat.openai.com/auth/login"

    def __init__(self):
        self.cookies_file_path = Path(__file__).parent / "cookies.pkl"

        # Set up Chrome options
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--user-agent=" + UserAgent().random)

        load_dotenv(override=True)
        self.email_address = os.getenv("CHATGPT_EMAIL")
        self.password = os.getenv("CHATGPT_PASSWORD")

    def query(self, prompt: str) -> str:

        driver = uc.Chrome(options=self.options)
        driver.get(self.chatgpt_url)

        try:
            cookies_exist = False

            if self.cookies_file_path.exists():
                cookies_exist = True
                try:
                    cookies = pickle.load(open(self.cookies_file_path, "rb"))
                    for cookie in cookies:
                        if cookie["name"] == "__Host-next-auth.csrf-token":
                            break
                        driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error loading cookies: {e}")

            driver.refresh()

            if not cookies_exist:
                print("Cookies not found, now logging in")
                wait = WebDriverWait(driver, 10)
                wait.until(EC.element_to_be_clickable((By.TAG_NAME, "button")))

                print("Page loaded")
                buttons = driver.find_elements(By.TAG_NAME, "button")
                login_button = None
                for button in buttons:
                    print(button.text)
                    if button.text.lower() == "log in":
                        login_button = button
                        break

                if login_button:
                    login_button.click()
                else:
                    raise Exception("Login button not found")

                wait.until(
                    EC.presence_of_element_located((By.ID, "email-input"))
                )

                mail = driver.find_element(By.ID, "email-input")
                mail.send_keys(self.email_address)

                btn = driver.find_element(By.CLASS_NAME, "continue-btn")
                btn.click()

                wait.until(EC.presence_of_element_located((By.ID, "password")))

                password = driver.find_element(By.ID, "password")
                password.send_keys(self.password)

                wait = WebDriverWait(driver, 10)
                btn = wait.until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, "_button-login-password")
                    )
                )
                btn.click()
            else:
                print("Cookies found, you should be logged in")

            print("Logged in")
            wait = WebDriverWait(driver, 180)
            wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "p.placeholder"))
            )
            prompt_input = driver.find_element(
                By.CSS_SELECTOR, "p.placeholder"
            )
            # sleep(3)
            # To paste the prompt (which bypasses return key issues)
            driver.execute_script(
                "arguments[0].innerText = arguments[1];", prompt_input, prompt
            )
            prompt_input.send_keys("\n")
            # sleep(10)
            # wait.until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, "div.prose"))
            # )
            # sleep(10)
            wait = WebDriverWait(driver, 60)
            response_div = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.prose"))
            )
            previous_response = ""
            start_time = time.time()
            current_response = ""
            # sleep(100)

            while True:
                sleep(2)
                try:
                    response_div = driver.find_element(
                        By.CSS_SELECTOR, "div.prose"
                    )
                    current_response = response_div.text
                except Exception as e:
                    print(
                        f"\033[91mError retrieving response text:\033[0m {e}"
                    )
                    sleep(2)
                if (
                    current_response == previous_response
                    or (time.time() - start_time) > 20
                ):
                    break
                previous_response = current_response

            print(current_response)

            pickle.dump(
                driver.get_cookies(), open(self.cookies_file_path, "wb")
            )
            print("Done")
            # sleep(100)
        except Exception as e:
            driver.quit()
            print(f"\033[91mError:\033[0m {e}")

        driver.quit()
        return current_response


if __name__ == "__main__":
    if len(sys.argv) == 2:
        message = sys.argv[1]
    else:
        message = TEST_PROMPT

    # Create an instance of XClient and post a tweet with an image
    chatgpt_client = ChatGPT()
    chatgpt_client.query(message)
