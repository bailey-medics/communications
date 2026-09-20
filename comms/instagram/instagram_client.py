import configparser
import os
import sys

from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired


class InstagramClient:
    def __init__(self):
        load_dotenv(override=True)

        # Reading Configs
        config = configparser.ConfigParser()
        config.read("config.ini")

        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")

    def requirements(self) -> list[str]:
        """Return the list of arguments that the post method takes.

        Returns:
            list[str]: The list of arguments that the post method takes.
        """
        return {"post": ["short_blurb", "image"], "max_text_length": 2200}

    def name(self) -> str:
        """Return the name of the client.

        Returns:
            str: The name of the client.
        """
        return "Instagram"

    def post(self, short_blurb: str, image: str):
        client = Client()
        try:
            client.login(self.username, self.password)
            client.photo_upload(image, caption=short_blurb)
        except LoginRequired:
            print("Login required. Please check your credentials.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Logout from Instagram
            client.logout()
            print("Instagram posted successfully")


if __name__ == "__main__":
    # Check for command-line arguments
    if len(sys.argv) == 3:
        short_blurb = sys.argv[1]
        image_path = sys.argv[2]
    else:
        short_blurb = "Hello World"
        # Construct the file path dynamically
        image_path = os.path.join(
            os.path.dirname(__file__), "../../media/ldd-logo.png"
        )
        image_path = os.path.abspath(image_path)

    # Create an instance of TwitterClient and post a tweet with an image
    instagram_client = InstagramClient()
    instagram_client.post(short_blurb, image_path)
