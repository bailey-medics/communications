import os
import re
import sys

from blueskysocial import Client, Image, Post
from dotenv import load_dotenv


class BlueskyClient:
    def __init__(self):
        load_dotenv(override=True)
        self.username = os.getenv("BLUESKY_USERNAME")
        self.password = os.getenv("BLUESKY_PASSWORD")

    def requirements(self) -> list[str]:
        """Return the list of arguments that the post method takes.

        Returns:
            dict[str:str]: The list of arguments that the post method takes.
        """
        return {
            "post": ["short_blurb", "image", "alt_text"],
            "max_text_length": 500,
            "max_image_size": 1000,
        }

    def name(self) -> str:
        """Return the name of the client.

        Returns:
            str: The name of the client.
        """
        return "Bluesky"

    def convert_hyperlinks(self, text: str) -> str:
        """Convert hyperlinks in the text to markdown format.

        Finds hyperlinks and converts to markdown format. It removes the http;//
        from the displayed name.
        """
        url_pattern = re.compile(r"(http[s]?://[^\s]+)")

        def replace_url(match):
            url = match.group(0)
            domain = url.split("//")[1]
            return f"[{domain}]({url})"

        # Replace URLs in the text
        return url_pattern.sub(replace_url, text)

    def post(self, short_blurb: str, image: str = "", alt_text: str = ""):
        client = Client()
        client.authenticate(self.username, self.password)
        converted_message = self.convert_hyperlinks(short_blurb)

        image = Image(image, alt_text=alt_text)
        post = Post(
            converted_message,
            with_attachments=[image],
        )
        client.post(post)
        print("Bluesky posted successfully")


if __name__ == "__main__":
    # Check for command-line arguments
    if len(sys.argv) == 4:
        short_blurb = sys.argv[1]
        image_path = sys.argv[2]
        alt_text = sys.argv[3]
    else:
        short_blurb = "Hello, world!, This is my first post.  But with a link.  http://letsdodigital.org"
        image_path = os.path.join(
            os.path.dirname(__file__), "../../media/ldd-logo.png"
        )
        image_path = os.path.abspath(image_path)
        alt_text = "Let's Do Digital logo"
        print("Using defaults...")

    bluesky_client = BlueskyClient()
    bluesky_client.post(short_blurb, image_path, alt_text)
