"""Facebook Client Module

Useful websites:

Developers (to create app): https://developers.facebook.com/apps
Create access tokens: https://developers.facebook.com/tools/explorer
Extend life of token: https://developers.facebook.com/tools/debug/accesstoken
Get page ID: TBC

"""

import os
import sys

import facebook
import requests
from dotenv import load_dotenv


class FacebookClient:
    def __init__(self):
        load_dotenv(override=True)
        self.access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")

    def requirements(self) -> list[str]:
        """Return the list of arguments that the post method takes.

        Returns:
            list[str]: The list of arguments that the post method takes.
        """
        return {"post": ["long_blurb", "image"], "max_text_length": 63206}

    def name(self) -> str:
        """Return the name of the client.

        Returns:
            str: The name of the client.
        """
        return "Facebook"

    def post(self, long_blurb: str, image: str) -> None:
        graph = facebook.GraphAPI(access_token=self.access_token)
        graph.put_photo(
            image=open(image, "rb"),
            message=long_blurb,
            profile_id=self.page_id,
        )
        print("Facebook posted successfully")

    # Function to post to Facebook
    def post_to_facebook(self, message):
        url = f"https://graph.facebook.com/{self.page_id}/feed"
        payload = {"message": message, "access_token": self.access_token}
        response = requests.post(url, data=payload)

        if response.status_code == 200:
            print("Facebook posted successfully")
        else:
            print(f"Error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        short_blurb = sys.argv[1]
        image_path = sys.argv[2]
    else:
        short_blurb = "Hello World!"
        # Construct the file path dynamically
        image_path = os.path.join(
            os.path.dirname(__file__), "../../media/ldd-logo.png"
        )
        image_path = os.path.abspath(image_path)

    # Create an instance of TwitterClient and post a tweet with an image
    facebook_client = FacebookClient()
    facebook_client.post(short_blurb, image_path)
