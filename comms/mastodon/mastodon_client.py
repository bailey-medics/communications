"""Mastodon client

Create app and get access token: https://mastodon.social/settings/applications
"""

import os
import sys

from dotenv import load_dotenv
from mastodon import Mastodon


class MastodonClient:
    client_secrets = "comms/mastodon/pytooter_clientcred.secret"
    word_limit = 500

    def __init__(self):
        load_dotenv(override=True)
        self.access_token = os.getenv("MASTODON_ACCESS_TOKEN")

    def register(self):
        """Register the app with Mastodon

        This needs to be only done once. It creates a secret file that is used to authenticate the app.

        """
        Mastodon.create_app(
            "pytooterapp",
            api_base_url="https://mastodon.social",
            to_file=self.client_secrets,
        )

    def requirements(self) -> list[str]:
        """Return the list of arguments that the post method takes.

        Returns:
            list[str]: The list of arguments that the post method takes.
        """
        return {
            "post": ["short_blurb", "image", "alt_text"],
            "max_text_length": 500,
            "max_image_size": 16000,
        }

    def name(self) -> str:
        """Return the name of the client.

        Returns:
            str: The name of the client.
        """
        return "Mastodon"

    def post(
        self, short_blurb: str, image: str = "", alt_text: str = ""
    ) -> None:
        """Post a message to Mastodon

        You can post a message with or without an image. If you post an image,
        you need to provide the path to the image.

        Args:
            short_blurb (str): The message to post.
            image (str): The path to the image to post.
            alt_text (str): The alt text for the image.
        Raises:
            ValueError: If the message exceeds the word limit.
        """
        if len(short_blurb) > self.word_limit:
            raise ValueError(
                f"Message exceeds {self.word_limit} character limit."
            )

        self.mastodon = Mastodon(
            access_token=self.access_token,
            api_base_url="https://mastodon.social",
        )

        if not image:
            self.mastodon.toot(short_blurb)
            return

        self.upload_image(image, alt_text)
        self.mastodon.status_post(short_blurb, media_ids=self.media)
        print("Mastodon posted successfully!")

    def upload_image(self, image, alt_text):
        self.media = self.mastodon.media_post(image, description=alt_text)


if __name__ == "__main__":
    if len(sys.argv) == 4:
        message = sys.argv[1]
        image = sys.argv[2]
        alt_text = sys.argv[3]
    else:
        message = "Hello World!"
        image = os.path.join(
            os.path.dirname(__file__), "../../media/ldd-logo.png"
        )
        image = os.path.abspath(image)
        alt_text = "LDD logo"

    # Create an instance of TwitterClient and post a tweet with an image
    mastodon_client = MastodonClient()
    mastodon_client.register()
    # mastodon_client.post(message, image, alt_text)
