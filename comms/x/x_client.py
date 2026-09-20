import os
import sys

import tweepy
from dotenv import load_dotenv


class XClient:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv(override=True)

        # Initialize the Tweepy client
        self.client = tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET_KEY"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        )

        # Authenticate to Twitter using OAuth1 for media upload
        auth = tweepy.OAuth1UserHandler(
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET_KEY"),
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        )

        self.api = tweepy.API(auth)

    def requirements(self) -> list[str]:
        """Return the list of arguments that the post method takes.

        Returns:
            list[str]: The list of arguments that the post method takes.
        """
        return {"post": ["short_blurb", "image"], "max_text_length": 280}

    def name(self) -> str:
        """Return the name of the client.

        Returns:
            str: The name of the client.
        """
        return "X"

    def post(self, short_blurb, image=""):
        # Upload the image
        media = self.api.media_upload(image)

        # TODO #7 need to check if there is a image added

        # Post a tweet with the image
        self.client.create_tweet(text=short_blurb, media_ids=[media.media_id])
        print("X posted successfully!")


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

    # Create an instance of XClient and post a tweet with an image
    twitter_client = XClient()
    twitter_client.post(short_blurb, image_path)
