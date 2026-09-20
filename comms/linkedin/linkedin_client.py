"""API client to post text and images to LinkedIn.

This module provides a LinkedInClient class that allows you to post text and
images to LinkedIn using the LinkedIn API. It includes methods for posting
updates with or without media.

Run `linkedin_get_access_token.py` to get an access token and store this as
`LINKEDIN_ACCESS_TOKEN` in a .env file.
"""

import os
import sys
from os.path import exists

import requests
from dotenv import load_dotenv


class LinkedinClient:
    """API client to post text and images to LinkedIn.

    This class provides methods to post text and images to LinkedIn using the
    LinkedIn API. You will need to store your credentials in a .env file.

    Attributes:
        access_token (str): The access token for LinkedIn API.
        user_urn (str): The uniform resource name of the LinkedIn person who is
                        signing in.
        images_ids (list[str]): A list to store uploaded image IDs.

    Methods:
        post(content: str, img_paths: str | list[str] | None = None) -> None:
            Posts an update to LinkedIn.
        upload_images(img_paths: str | list[str]) -> None:
            Uploads images to LinkedIn and stores their IDs.
    """

    def __init__(self) -> None:
        """Initializes the LinkedInClient with access token and user URN."""
        load_dotenv(override=True)
        self.access_token: str = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.user_urn: str = os.getenv("LINKEDIN_PERSON_URN")
        self.images_ids: list[str] = []

    def requirements(self) -> list[str]:
        """Return the list of arguments that the post method takes.

        Returns:
            list[str]: The list of arguments that the post method takes.
        """
        return {"post": ["long_blurb", "image"], "max_text_length": 3000}

    def name(self) -> str:
        """Return the name of the client.

        Returns:
            str: The name of the client.
        """
        return "LinkedIn"

    def post(
        self, long_blurb: str, image: str | list[str] | None = None
    ) -> None:
        """Posts an update to LinkedIn.

        Args:
            long_blurb (str): The text content of the post.
            image (str | list[str] | None): The path to the image file or
                                                a list of image file paths to
                                                be uploaded.
        """

        api_url: str = "https://api.linkedin.com/v2/ugcPosts"

        headers: dict[str:str] = {
            "Authorization": f"Bearer {self.access_token}",
            "Connection": "Keep-Alive",
            "Linkedin-Version": "format AAAAMM",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        media: dict[str:str] = {"shareMediaCategory": "NONE"}

        if image:
            self.upload_images(image)
            media = {
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "media": img_id,
                    }
                    for img_id in self.images_ids
                ],
            }

        post_body: dict[str:str] = {
            "author": f"urn:li:person:{self.user_urn}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": long_blurb},
                    **media,
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        # print(post_body)

        response: requests.Response = requests.post(
            api_url, headers=headers, json=post_body
        )
        if response.status_code == 201:
            print("LinkedIn posted successfully")

        else:
            print(f"{response.status_code}: {response.text}")
            sys.exit(1)

    def upload_images(self, img_paths: str | list[str]) -> None:
        """Uploads images to LinkedIn and stores their IDs.

        Args:
            img_paths (Union[str, List[str]]): The path(s) to the image(s) to
                                               upload.
        """
        # print(img_paths)
        if isinstance(img_paths, str):
            img_paths = [img_paths]
        # print(img_paths)

        upload_headers: dict[str:str] = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream",
        }

        for image_file_path in img_paths:
            if not exists(image_file_path):
                print(f"Image file not found: {image_file_path}")
                sys.exit(1)

            payload: dict[str:str] = {
                "registerUploadRequest": {
                    "owner": f"urn:li:person:{self.user_urn}",
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "serviceRelationships": [
                        {
                            "identifier": "urn:li:userGeneratedContent",
                            "relationshipType": "OWNER",
                        }
                    ],
                }
            }
            register_post: requests.Response = requests.post(
                f"https://api.linkedin.com/v2/assets?action=registerUpload&oauth2_access_token={self.access_token}",
                json=payload,
            ).json()

            # print(register_post)

            if (
                "serviceErrorCode" in register_post
                and register_post["serviceErrorCode"] == 65602
            ):
                raise ValueError("The token used in the request has expired")

            upload_url: str = register_post["value"]["uploadMechanism"][
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
            ]["uploadUrl"]

            requests.post(
                upload_url,
                headers=upload_headers,
                data=open(image_file_path, "rb"),
            )

            self.images_ids.append(register_post["value"]["asset"])

        # print(self.images_ids)


if __name__ == "__main__":
    client = LinkedinClient()

    if len(sys.argv) == 3:
        message: str = sys.argv[1]
        image_path: str = sys.argv[2]
    else:
        message: str = "Hello, LinkedIn! Here is a picture."
        image_path: str = "../../media/ldd-logo.png"

    client.post(message, image_path)
